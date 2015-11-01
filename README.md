###修改

主要添加使用了Key，Gamebox和Round

有一些旧的关联的filed还没有删掉，后面准备删掉

一个Key对应一个Gamebox Round Challenge

统一提交接口，只需要提交Key即可判断情况见challenge.py submit_flag


###前端TODO

把每个题目的提交窗口去掉，统一放在challenge显示页面的下方，ajax接口小改动参照submit_flag函数的返回情况。

###后端TODO

修改积分计算逻辑

去掉没有用的代码