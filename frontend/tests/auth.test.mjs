import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const srcRoot = path.resolve(new URL('../src/', import.meta.url).pathname)

test('logout uses the server session endpoint with cookie credentials', async () => {
  const apiSource = await fs.readFile(path.join(srcRoot, 'api.js'), 'utf8')
  assert.match(apiSource, /logout:\s*\(\)\s*=>\s*request\('\/api\/v1\/auth\/logout',\s*\{\s*method:\s*'POST'\s*\}\)/)
  assert.match(apiSource, /credentials:\s*'include'/)
})

test('authenticated app has guarded logout state and a mobile logout action', async () => {
  const appSource = await fs.readFile(path.join(srcRoot, 'App.jsx'), 'utf8')
  assert.match(appSource, /const \[logoutBusy, setLogoutBusy\] = useState\(false\)/)
  assert.match(appSource, /if \(logoutBusy \|\| !window\.confirm\(/)
  assert.match(appSource, /setLogoutBusy\(true\)/)
  assert.match(appSource, /setSession\(null\)/)
  assert.match(appSource, /className="logout-button"/)
  assert.match(appSource, /className="mobile-logout"/)
  assert.match(appSource, /disabled=\{logoutBusy\}/)
  assert.match(appSource, /Signing out/)
})

test('logout does not require browser-stored bearer tokens', async () => {
  const apiSource = await fs.readFile(path.join(srcRoot, 'api.js'), 'utf8')
  const appSource = await fs.readFile(path.join(srcRoot, 'App.jsx'), 'utf8')
  assert.equal(/Authorization:\s*Bearer/i.test(apiSource + appSource), false)
})
