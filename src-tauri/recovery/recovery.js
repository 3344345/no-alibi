const reason = new URLSearchParams(location.search).get('reason') || 'starting'
const descriptions = {
  component: '启动所需的本地组件缺失或无法读取。可从完整的应用程序包重新打开。',
  handshake: '本地引擎没有及时完成连接。',
  startup: '档案目录或本地引擎未能打开。',
  archive: '所选备份未通过版本或完整性校验。请重新选择一份完整的游戏存档。',
  storage: '本地档案目录暂时无法写入。请检查可用空间和文件访问权限。',
  exited: '本地引擎已意外停止。重试后可从最近一次已提交的行动继续。',
  window: '游戏窗口未能显示本地引擎。'
}
const controls = document.getElementById('controls')
const statusLine = document.getElementById('status')
const file = document.getElementById('file')
if (reason !== 'starting') {
  document.getElementById('heading').textContent = '启动恢复'
  document.getElementById('explanation').textContent = descriptions[reason] || '暂时无法打开当前生涯。'
  controls.hidden = false
}
const invoke = (name, args={})=>window.__TAURI_INTERNALS__.invoke(name,args)
async function start(archive) {
  controls.hidden=true
  statusLine.textContent=archive===null?'正在重试…':'正在校验备份并打开独立档案…'
  try { await invoke('recover_engine',{archive}) }
  catch(error){ controls.hidden=false; statusLine.textContent=String(error) }
}
document.getElementById('retry').addEventListener('click',()=>start(null))
file.addEventListener('change',async()=>{
  const selected=file.files[0];if(!selected)return
  try{await start(await selected.text())}catch{statusLine.textContent='所选文件无法读取。'}finally{file.value=''}
})
document.getElementById('diagnostic').addEventListener('click',async()=>{
  try{statusLine.textContent=await invoke('save_diagnostic');document.getElementById('reveal').hidden=false}
  catch(error){statusLine.textContent=String(error)}
})
document.getElementById('reveal').addEventListener('click',async()=>{
  try{await invoke('reveal_diagnostic')}catch(error){statusLine.textContent=String(error)}
})
