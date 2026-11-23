import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const srcDir = path.resolve(__dirname, '..', 'dist')
const destDir = path.resolve(__dirname, '..', '..', 'backend', 'static')

try {
  if (!fs.existsSync(srcDir)) {
    console.error(`❌ dist 폴더가 존재하지 않습니다: ${srcDir}`)
    process.exit(1)
  }

  // backend/static 폴더 생성
  fs.mkdirSync(destDir, { recursive: true })

  // dist 폴더 내용을 backend/static으로 복사
  fs.cpSync(srcDir, destDir, { recursive: true, force: true })

  console.log(`✅ [자동 복사 완료] 'dist' -> 'backend/static' (${destDir})`)
} catch (err) {
  console.error(`❌ 복사 중 오류 발생:`, err)
  process.exit(1)
}
