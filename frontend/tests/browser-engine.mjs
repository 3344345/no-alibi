import { spawn } from 'node:child_process'
import { once } from 'node:events'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createInterface } from 'node:readline'
import { fileURLToPath } from 'node:url'
import { chromium, webkit } from 'playwright-core'

const root = fileURLToPath(new URL('../../', import.meta.url))

/** Uses an isolated, persistent SQLite profile. The renderer never opens a native window. */
export async function startBrowserFixture() {
  const profile = await mkdtemp(join(tmpdir(), 'jzs-browser-'))
  const bundle = process.env.JZS_TEST_APP
  const env = { ...process.env }
  if (bundle) {
    delete env.PYTHONPATH
    delete env.PYTHONHOME
  }
  let child, browser, session
  async function stop() {
    if (child?.exitCode === null && child.signalCode === null) {
      const ended = once(child, 'exit')
      child.kill()
      await ended
    }
    child = undefined
  }
  async function start() {
    const executable = bundle
      ? join(bundle, 'Contents/MacOS/jzs-engine')
      : process.env.PYTHON || join(root, '.venv/bin/python')
    const args = bundle ? ['--assets', join(bundle, 'Contents/Resources/web')] : ['main.py']
    child = spawn(executable, [...args, '--no-browser', '--data-dir', profile], {
      cwd: bundle ? profile : root,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    let stderr = ''
    child.stderr.on('data', (data) => {
      stderr = (stderr + data).slice(-2000)
    })
    const stdout = createInterface({ input: child.stdout })
    try {
      const [entry] = await Promise.race([
        once(stdout, 'line'),
        once(child, 'exit').then(([code]) => {
          throw Error('Local test engine exited (' + code + '): ' + stderr)
        }),
      ])
      session = String(entry)
      if (new URL(session).hostname !== '127.0.0.1') throw Error('Expected a loopback game engine')
    } finally {
      stdout.close()
    }
  }
  async function close() {
    try {
      await browser?.close()
    } finally {
      try {
        await stop()
      } finally {
        await rm(profile, { recursive: true, force: true })
      }
    }
  }
  try {
    await start()
    browser =
      process.env.JZS_BROWSER === 'webkit'
        ? await webkit.launch({ headless: true })
        : await chromium.launch({
            headless: true,
            ...(process.env.CHROME_BIN ? { executablePath: process.env.CHROME_BIN } : { channel: 'chrome' }),
          })
    return {
      profile,
      browser,
      get session() {
        return session
      },
      get address() {
        return new URL(session).origin
      },
      async restart() {
        await stop()
        await start()
      },
      close,
    }
  } catch (error) {
    await close()
    throw error
  }
}
