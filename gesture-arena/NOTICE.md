# 第一方與第三方資源

角色、效果及網站樣式由第一方程式產生，沒有外部CDN、商標素材或下載圖片。第一方原始碼交付供本工作坊使用與修改。

安裝套件及相應授權隨npm套件保存：React、Phaser、Vite、TypeScript、Socket.IO、Express、dotenv、tsx、Vitest及Playwright。確切版本由package-lock.json固定；重新散布第三方套件時保留各套件附帶LICENSE／NOTICE。

SQLite使用Node22.19.0的node:sqlite，該固定版本會顯示experimental警告。更換Node或依賴版本後，重新執行建置、核心、瀏覽器與長測驗收。
