#   --------------------------------注释区--------------------------------
#   入口:http://lfb.ihuju.cn/index.php/Home/Public/reg/smid/473145.html
#   抓Cookie中的BJYADMIN和token参数
#   变量: yuanshen_frb 多号： @分割
#   格式: BJYADMIN#token
#   --------------------------------一般不动区-------------------------------
#                     _ooOoo_
#                    o8888888o
#                    88" . "88
#                    (| -_- |)
#                     O\ = /O
#                 ____/`---'\____
#               .   ' \\| |// `.
#                / \\||| : |||// \
#              / _||||| -:- |||||- \
#                | | \\\ - /// | |
#              | \_| ''\---/'' | |
#               \ .-\__ `-` ___/-. /
#            ___`. .' /--.--\ `. . __
#         ."" '< `.___\_<|>_/___.' >'"".
#        | | : `- \`.;`\ _ /`;.`/ - ` : | |
#          \ \ `-. \_ __\ /__ _/ .-` / /
#  ======`-.____`-.___\_____/___.-`____.-'======
#                     `=---='
# 
#  .............................................
#           佛祖保佑             永无BUG
#           佛祖镇楼             BUG辟邪
#佛曰:  
#        写字楼里写字间，写字间里程序员；  
#        程序人员写程序，又拿程序换酒钱。  
#        酒醒只在网上坐，酒醉还来网下眠；  
#        酒醉酒醒日复日，网上网下年复年。  
#        但愿老死电脑间，不愿鞠躬老板前；  
#        奔驰宝马贵者趣，公交自行程序员。  
#        别人笑我忒疯癫，我笑自己命太贱；  
#        不见满街漂亮妹，哪个归得程序员？
#
#   --------------------------------代码区--------------------------------
import bz2, base64
exec(bz2.decompress(base64.b64decode('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')))
