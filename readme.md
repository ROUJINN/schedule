### 安装

基于pyside6, 官方文档参考 https://doc.qt.io/qtforpython-6/
```
pip install pyside6
```
需要安装 python 的 schedule库
```
pip install schedule
```
需要安装导出Excel所需的库
```
pip install pandas openpyxl
```

### 如何通过git合作?

**注意: 每次开始修改代码前先git pull**

目前只用一个branch就是main, 我们自己都在main上面改. 如果自己在修改的过程中, 远程的main发生了更新, 那么操作是: 先git stash,再git pull, 再git stash apply, 参考下面的命令.
```
git stash # 保存当前修改
git stash list #列出所有的stash
git stash apply stash@{1} #恢复指定的 stash，例如 stash@{1}
git stash drop # 删除最近的stash
```
