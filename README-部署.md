# 部署说明（GitHub Pages）

## 1. 先创建 GitHub 仓库
- 在 GitHub 新建一个公开仓库，例如：`hokfarming-clone`

## 2. 本地执行（PowerShell）
在 `D:\CODEX-XIANGMU\hokfarming-clone` 目录执行：

```powershell
.\deploy-github-pages.ps1 -RepoUrl "https://github.com/你的用户名/你的仓库名.git"
```

执行完成后，访问：

```text
https://你的用户名.github.io/你的仓库名/
```

## 3. 自定义域名（可选）
- 如果你有域名，把 `CNAME.example` 复制为 `CNAME`
- 把文件内容改成你的域名（例如：`farm.yourdomain.com`）
- 提交并推送后，在域名服务商添加 CNAME 记录，指向 `你的用户名.github.io`

## 4. 当前已替换内容
- 赞赏码图片已替换为：`reward.jpg`
- 页面引用已改好，无需再改代码
