/** Keep already-open player windows in sync without exposing the session in a URL. */
export function watchWorld(id: string, revision: () => number, update: (n: number) => Promise<void>) {
  const controller = new AbortController()
  const { signal } = controller
  const pause = () =>
    new Promise<void>((resolve) => {
      const finish = () => {
        clearTimeout(timer)
        signal.removeEventListener('abort', finish)
        resolve()
      }
      const timer = setTimeout(finish, 1800)
      signal.addEventListener('abort', finish, { once: true })
    })
  async function run() {
    while (!signal.aborted) {
      try {
        const key = sessionStorage.getItem('jzs-local-session')
        const response = await fetch(
          '/api/worlds/' + encodeURIComponent(id) + '/events?after=' + revision(),
          {
            signal,
            headers: key ? { Authorization: 'Bearer ' + key } : {},
            cache: 'no-store',
          },
        )
        if (!response.ok || !response.body) {
          if ([401, 403, 404].includes(response.status)) return
          throw Error('stream')
        }
        const reader = response.body.getReader(),
          decoder = new TextDecoder()
        let remainder = ''
        try {
          while (!signal.aborted) {
            const data = await reader.read()
            if (data.done) break
            remainder += decoder.decode(data.value, { stream: true })
            let end: number
            while ((end = remainder.indexOf('\n\n')) >= 0) {
              const block = remainder.slice(0, end)
              remainder = remainder.slice(end + 2)
              const line = block.split('\n').find((l) => l.startsWith('id:'))
              if (line) {
                const n = Number(line.slice(3))
                if (Number.isInteger(n) && n > revision()) await update(n)
              }
            }
          }
        } finally {
          reader.releaseLock()
        }
      } catch {
        /* Reconnect from the last applied revision when local service returns. */
      }
      if (!signal.aborted) await pause()
    }
  }
  void run()
  return () => controller.abort()
}
