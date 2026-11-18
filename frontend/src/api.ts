const secretKey = 'jzs-local-session'
const fragment = new URLSearchParams(location.hash.slice(1))
const supplied = fragment.get('session')
if (supplied) {
  sessionStorage.setItem(secretKey, supplied)
  history.replaceState(null, '', location.pathname + location.search)
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}
async function request(path: string, body?: unknown, descriptor?: { raw?: string }) {
  const secret = sessionStorage.getItem(secretKey)
  const headers = new Headers()
  if (secret) headers.set('Authorization', 'Bearer ' + secret)
  if (body !== undefined || descriptor?.raw !== undefined)
    headers.set('Content-Type', 'application/json')
  const response = await fetch('/api' + path, {
    method: body === undefined && descriptor?.raw === undefined ? 'GET' : 'POST',
    headers,
    body: descriptor?.raw ?? (body === undefined ? undefined : JSON.stringify(body)),
    cache: 'no-store',
    signal: AbortSignal.timeout(120000),
  })
  if (!response.ok) {
    let detail: unknown
    try {
      const payload = await response.json()
      detail = payload.detail ?? payload.message ?? payload.error
    } catch {
      /* use local status */
    }
    const defaults: Record<number, string> = {
      400: '输入格式有误，请检查后重新提交。',
      401: '连接凭据已失效，请从游戏启动器再次打开。',
      403: '本次操作缺少授权。',
      404: '没有找到对应的档案或事项。',
      409: '档案已经更新，请重新检查当前状态。',
      413: '存档文件超过了导入大小限制。',
      422: '提交内容不符合当前操作的要求。',
    }
    throw new ApiError(
      response.status,
      typeof detail === 'string' ? detail : defaults[response.status] || '本地引擎没有完成本次请求。',
    )
  }
  return response
}
export async function api<T>(path: string, body?: unknown): Promise<T> {
  return (await request(path, body)).json()
}
export async function download(path: string): Promise<Blob> {
  return (await request(path)).blob()
}
export function message(e: unknown) {
  return e instanceof ApiError ? e.message : '暂时无法连接本地引擎。请检查启动器后重试。'
}

/** Preserve exact numbers and signed values when restoring a game archive. */
export async function importSave<T>(raw: string): Promise<T> {
  return (await request('/import', undefined, { raw })).json()
}
