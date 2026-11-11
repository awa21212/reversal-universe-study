param(
  [Parameter(Mandatory=$true)][string]$Url,
  [string]$Proxy = "",
  [string]$Branch = "main"
)
# 用法：
#   .\push.ps1 -Url https://github.com/你的用户名/reversal-universe-study.git
#   走代理： .\push.ps1 -Url https://github.com/... -Proxy http://127.0.0.1:7892
$ErrorActionPreference = "Stop"
$env:GIT_TERMINAL_PROMPT = "1"
git branch -M $Branch 2>$null
$exist = (git remote 2>$null) -contains "origin"
if ($exist) { git remote set-url origin $Url } else { git remote add origin $Url }
if ($Proxy -ne "") {
    git -c "http.proxy=$Proxy" -c "https.proxy=$Proxy" push -u origin $Branch
} else {
    git push -u origin $Branch
}
if ($LASTEXITCODE -eq 0) { "✅ 已推送：$Url" } else { "❌ 推送失败，检查网络/代理/凭据" }
