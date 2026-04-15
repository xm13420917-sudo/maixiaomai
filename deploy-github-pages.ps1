param(
  [Parameter(Mandatory = $true)]
  [string]$RepoUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $scriptDir

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "未检测到 git，请先安装 Git。"
}

if (-not (Test-Path -LiteralPath ".git")) {
  git init | Out-Null
}

git add . | Out-Null
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
  git commit -m "chore: initial publish" | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "git commit 失败，请先配置 Git 用户名和邮箱。"
  }
}

git branch -M main | Out-Null

$hasOrigin = git remote 2>$null | Select-String -Pattern "^origin$" -Quiet
if (-not $hasOrigin) {
  git remote add origin $RepoUrl
} else {
  git remote set-url origin $RepoUrl
}

git push -u origin main

Write-Host ""
Write-Host "推送完成。"
Write-Host "请在 GitHub 仓库 Settings -> Pages 中："
Write-Host "1) Source 选择 'Deploy from a branch'"
Write-Host "2) Branch 选择 'main' / '/ (root)'"
Write-Host ""
