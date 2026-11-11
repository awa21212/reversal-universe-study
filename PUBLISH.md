# 发布说明

代码已提交到本地仓库（分支待命名 main），只差 push。

## 当前网络状况（2026-11-11 实测）

| 目标 | 结果 |
|---|---|
| `github.com:443` | ❌ 不可达（校园网） |
| `api.github.com` | ✅ 可达 |
| `ssh.github.com:443` | ✅ 可达 |
| `gitee.com:443` | ✅ 可达 |
| 本地代理 `127.0.0.1:7892` | ❌ 没在监听（ProxyEnable=0） |

## 三条路

### A. 开代理（最快）

1. 打开你的代理工具（配置里写着 `127.0.0.1:7892`），确认它开始监听；
2. 回到本目录执行：

```powershell
.\push.ps1 -Url https://github.com/<你的用户名>/reversal-universe-study.git -Proxy http://127.0.0.1:7892
```

3. 首次 push 会弹浏览器让你登录 GitHub（Git Credential Manager）。

### B. 走 SSH over 443（不用代理，但要先配 key）

```powershell
ssh-keygen -t ed25519 -C "you@example.com"      # 一路回车
# 把 ~/.ssh/id_ed25519.pub 的内容加到 GitHub → Settings → SSH keys（这一步需要能上网）
git remote add origin git@github.com:<用户名>/reversal-universe-study.git
git -c core.sshCommand="ssh -p 443 -o Hostname=ssh.github.com" push -u origin main
```

### C. 先推 Gitee，之后再镜像到 GitHub

```powershell
.\push.ps1 -Url https://gitee.com/<你的用户名>/reversal-universe-study.git
# 之后在任意能上网的机器上：git remote add github ... && git push github main
```

## 需要一个前提

两种方式都需要你先在 GitHub/Gitee 上**建一个空仓库**（不勾 README）。仓库名建议 `reversal-universe-study`。
