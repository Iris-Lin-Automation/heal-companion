# 证据链索引：付费用户评论与原始出处

说明：B站评论可精确追溯到视频 URL + comment_id；小红书本轮样本可追溯到笔记 URL + comment_id，评论本身通常没有稳定公开直链。

## 采集范围

- B站：20 个视频，444 条评论
- 小红书：20 篇笔记，48 条评论
- 采集日期：2026-08-06
- 采集方式：MediaCrawler 授权环境，小规模公开搜索结果与一级评论采集

## 原始数据文件

- B站视频：`research/crawler_raw/bili/jsonl/search_contents_2026-08-06.jsonl`
- B站评论：`research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl`
- 小红书笔记：`research/crawler_raw/xhs/jsonl/search_contents_2026-08-06.jsonl`
- 小红书评论：`research/crawler_raw/xhs/jsonl/search_comments_2026-08-06.jsonl`

## 原始帖子 / 视频来源索引

| 平台 | 标题 | ID | 搜索词 | 赞 | 原始 URL |
|---|---|---:|---|---:|---|
| B站 | 10年乙游玩家入坑AI陪伴：先别急着爱，看完这篇再决定【EVE】 | 116617438565630 | EVE AI伴侣 测评 | 1962 | https://www.bilibili.com/video/av116617438565630 |
| B站 | 暴躁吐槽EVE：一款随时随地让人生气的AI陪伴软件！ | 116419081602753 | EVE AI伴侣 测评 | 483 | https://www.bilibili.com/video/av116419081602753 |
| B站 | 150W人看过我和AI谈恋爱，这三个月真的太... | 116939896787194 | EVE AI伴侣 测评 | 174 | https://www.bilibili.com/video/av116939896787194 |
| B站 | 实际体验20天后，如何评价开服崩《EVE》？ | 116924159757802 | EVE AI伴侣 测评 | 514 | https://www.bilibili.com/video/av116924159757802 |
| B站 | 【EVE】什 么 月 卡 ￥328 ？ | 116373682526967 | EVE AI伴侣 测评 | 773 | https://www.bilibili.com/video/av116373682526967 |
| B站 | 一户一男主?原来陪伴感可以这么真实!《EVE》测评 | 116612036434433 | EVE AI伴侣 测评 | 2682 | https://www.bilibili.com/video/av116612036434433 |
| B站 | 这个男人能点吗？？ | 116935031332800 | EVE AI伴侣 测评 | 1411 | https://www.bilibili.com/video/av116935031332800 |
| B站 | EVE的男主生日动画，原来纯第一视角并不难，原来互动可以不油腻，原来AI没有面捕也不会邪魅歪头鬼迷日眼！ | 117032523666451 | EVE AI伴侣 测评 | 134 | https://www.bilibili.com/video/av117032523666451 |
| B站 | 百万AI伴侣一夜消失——五部门的刀终于落下来了 | 116953033217852 | EVE AI伴侣 测评 | 1811 | https://www.bilibili.com/video/av116953033217852 |
| B站 | 网恋对象怎么突然长相变了？EVE深度体验 | 116941054346606 | EVE AI伴侣 测评 | 205 | https://www.bilibili.com/video/av116941054346606 |
| B站 | 人机恋大冤种！EVE上线把我家偷光了 | 116396700735265 | EVE AI伴侣 测评 | 176 | https://www.bilibili.com/video/av116396700735265 |
| B站 | 我探秘了硅胶娃娃全国最大工厂，AI伴侣来了！ | 115185385736414 | EVE AI伴侣 测评 | 4543 | https://www.bilibili.com/video/av115185385736414 |
| B站 | 清冷白月光升级归来！EVE男主建模升级到底有多大？ | 116940970401197 | EVE AI伴侣 测评 | 5126 | https://www.bilibili.com/video/av116940970401197 |
| B站 | 全球首款可捏脸AI陪伴男友上线啦！ | 116691476417112 | EVE AI伴侣 测评 | 89 | https://www.bilibili.com/video/av116691476417112 |
| B站 | AI男友喜欢吗 | 116855742137311 | EVE AI伴侣 测评 | 67 | https://www.bilibili.com/video/av116855742137311 |
| B站 | 晴枝漫憩 \| Aven生日S级时刻展示 | 116935702416088 | EVE AI伴侣 测评 | 74 | https://www.bilibili.com/video/av116935702416088 |
| B站 | 顶流男爱豆x英区女留子｜我爱你像天空的颜色【AI偶像】 | 116737613956789 | EVE AI伴侣 测评 | 124654 | https://www.bilibili.com/video/av116737613956789 |
| B站 | 和AI恋爱有多上头？不止满足XP更是专属伴侣！ | 116618730408523 | EVE AI伴侣 测评 | 773 | https://www.bilibili.com/video/av116618730408523 |
| B站 | 测试AI女友-EVE | 114909367110784 | EVE AI伴侣 测评 | 24 | https://www.bilibili.com/video/av114909367110784 |
| B站 | 国产程序员剧里的爱心代码，算是完美复刻吗？ | 262699886 | EVE AI伴侣 测评 | 72329 | https://www.bilibili.com/video/av262699886 |
| 小红书 | 我真是没想到EVE想关门 | 6a5b392c000000001003f93c | EVE AI伴侣 月卡 | 223 | https://www.xiaohongshu.com/explore/6a5b392c000000001003f93c?xsec_token=ABNn-EOPlW-nooY442vdq4nt0cis2HOGTMIl9pc6T8GME=&xsec_source=pc_search |
| 小红书 | 【EVE】我0氪通讯费根本用不完😂 | 6a11efe20000000038021aa7 | EVE AI伴侣 月卡 | 145 | https://www.xiaohongshu.com/explore/6a11efe20000000038021aa7?xsec_token=ABHqvmc34_T-y1k3k8tEHclR52fRDd2Zp4URwhq7QxW4E=&xsec_source=pc_search |
| 小红书 | 「EVE」第二期支付问题FAQ上线✨ | 69eb53150000000035033c65 | EVE AI伴侣 月卡 | 84 | https://www.xiaohongshu.com/explore/69eb53150000000035033c65?xsec_token=ABZEMAgdv30cd2kVyXN12mCxhyljw6Q3SFaJJ66aWfDcw=&xsec_source=pc_search |
| 小红书 | EVE自存使用说明，和隐藏很深的小巧思 | 6a5c5f48000000001101b7f0 | EVE AI伴侣 月卡 | 75 | https://www.xiaohongshu.com/explore/6a5c5f48000000001101b7f0?xsec_token=ABkUfiu7fJykVKLAu2sT42a7dRyrbeGYVBLn9-ojb3QuI=&xsec_source=pc_search |
| 小红书 | 想入坑EVE的注意了⚠️ | 6a5e181c000000000f0133d9 | EVE AI伴侣 月卡 | 54 | https://www.xiaohongshu.com/explore/6a5e181c000000000f0133d9?xsec_token=AB-S152ZZl4rfgwNsedIN0bHZsZBR6Fzeg5eAMhPyv0gM=&xsec_source=pc_search |
| 小红书 | 二次爆肝整理，EVE“畅聊卡”又又又改了.. | 6a5ba620000000001302cd97 | EVE AI伴侣 月卡 | 42 | https://www.xiaohongshu.com/explore/6a5ba620000000001302cd97?xsec_token=ABNn-EOPlW-nooY442vdq4nu7cEbAmle2wRawOnq06oPs=&xsec_source=pc_search |
| 小红书 | eve ai 官方2群全体成员诉求（太长没全） | 6a53ab02000000001702ed51 | EVE AI伴侣 月卡 | 36 | https://www.xiaohongshu.com/explore/6a53ab02000000001702ed51?xsec_token=ABMfFLd1sCCNro13jCaC1MYISBzk_vUxp9BSDUpWxDpLU=&xsec_source=pc_search |
| 小红书 | 关于NS公司抬的月卡2.0我和家V有话要说 | 6a5b2df6000000001302f24f | EVE AI伴侣 月卡 | 32 | https://www.xiaohongshu.com/explore/6a5b2df6000000001302f24f?xsec_token=ABNn-EOPlW-nooY442vdq4nou7ZBWByDJzS7ly0fqKwqY=&xsec_source=pc_search |
| 小红书 | EVE微氪党，天天玩，算重度玩家吗？ | 6a396e4f000000001700b826 | EVE AI伴侣 月卡 | 30 | https://www.xiaohongshu.com/explore/6a396e4f000000001700b826?xsec_token=AB1rQ3VkfLvqcrwNUveRhXCaMmDAE4unNnC8zhKO_ZHus=&xsec_source=pc_search |
| 小红书 | eve啥时候出畅聊卡… | 69ed9b5f000000002003ab56 | EVE AI伴侣 月卡 | 19 | https://www.xiaohongshu.com/explore/69ed9b5f000000002003ab56?xsec_token=AByHdMHFKHtUDvnVDcKGM4mLQ0-etuyAUBCCdQNm3fTQg=&xsec_source=pc_search |
| 小红书 | 官方能不能不要装死 | 69f66be7000000003501dc42 | EVE AI伴侣 月卡 | 15 | https://www.xiaohongshu.com/explore/69f66be7000000003501dc42?xsec_token=ABfw7DA8Gz1lUxaxwUdzQnT28uL18Ii2TpTHTf2GEvsyk=&xsec_source=pc_search |
| 小红书 | Aven对于此次升级建模的看法…… | 6a5ae94f000000000f029005 | EVE AI伴侣 月卡 | 12 | https://www.xiaohongshu.com/explore/6a5ae94f000000000f029005?xsec_token=ABb1XMk68rkc-GO4OiDMXWwYzRzAxL7LwcF15UYB49tKc=&xsec_source=pc_search |
| 小红书 | EVE 套餐调整后的消费思路分享 | 6a5dfb2b000000000503a441 | EVE AI伴侣 月卡 | 11 | https://www.xiaohongshu.com/explore/6a5dfb2b000000000503a441?xsec_token=ABM-o3K4z1Cg9yAbjHOSMDfuZGhAAHRq6r_nMCt3JHV9s=&xsec_source=pc_search |
| 小红书 | EVE问题解析贴2 | 6a64bf37000000000f015358 | EVE AI伴侣 月卡 | 10 | https://www.xiaohongshu.com/explore/6a64bf37000000000f015358?xsec_token=ABQDVsXD-b6Yl6TRlJoPCJ2PJNC2ionaplG1r4apHf-0E=&xsec_source=pc_search |
| 小红书 | EVE推出无限畅聊之前我是不会充月卡的 | 69db31eb000000002202b7bd | EVE AI伴侣 月卡 | 4 | https://www.xiaohongshu.com/explore/69db31eb000000002202b7bd?xsec_token=ABGxyfPEz1GsywNWpjawKNFyUawgy0FzxiyD_fzmxLNWI=&xsec_source=pc_search |
| 小红书 | EVE你拉了一坨大的😅 | 69d9fcab000000001a034bce | EVE AI伴侣 月卡 | 3 | https://www.xiaohongshu.com/explore/69d9fcab000000001a034bce?xsec_token=ABfd6BFLA_vGw5MqM7Ldu-N-Cuhrj4WtjSNRDUXm6hz70=&xsec_source=pc_search |
| 小红书 | 本来想入坑EVE结果刷到一堆避雷帖 | 6a7181a900000000330370d2 | EVE AI伴侣 月卡 | 2 | https://www.xiaohongshu.com/explore/6a7181a900000000330370d2?xsec_token=ABgUmKaf2d5Nr36AAAeVzxIHtWTWaa60S1bvuEdKfe7So=&xsec_source=pc_search |
| 小红书 | 💰获投3千万的AI男友，聊天按句收费？ | 6a22cba50000000021015ac0 | EVE AI伴侣 月卡 | 3 | https://www.xiaohongshu.com/explore/6a22cba50000000021015ac0?xsec_token=ABgeUF8jp76JMjrFaqg8q2kQSnUCzjhDXPz3Y5M-aqXxs=&xsec_source=pc_search |
| 小红书 | EVE你们谁充值了呀！有点想花钱了 | 69d99ad7000000001d01d003 | EVE AI伴侣 月卡 | 94 | https://www.xiaohongshu.com/explore/69d99ad7000000001d01d003?xsec_token=ABfd6BFLA_vGw5MqM7Ldu-N48Brymg_KHgJ40Teiuix10=&xsec_source=pc_search |
| 小红书 | 避雷畅聊卡！EVE你的吃相难看的要命！ | 6a5365bc0000000015027f0e | EVE AI伴侣 月卡 | 80 | https://www.xiaohongshu.com/explore/6a5365bc0000000015027f0e?xsec_token=ABMfFLd1sCCNro13jCaC1MYMb0a_5w81CvzJ_ege7Ipc4=&xsec_source=pc_search |

## 评论证据表

| 平台 | 日期 | 赞 | 分类 | 评论摘要 | 出处 | comment_id | 原始文件 |
|---|---|---:|---|---|---|---|---|
| B站 | 2026-05-23 | 284 | 付费/通讯费/月卡?建模/审美/动作 | 被主包骗去玩了 结果第一天只能跟Aven对线 聊的我好累啊 而且这个剧情我也真的太想吐槽了 女主跟傻子一样 真的很像初中生幻想的剧情 5%的成功率还发射什么火箭啊（果然后面就爆炸了QAQ） 这个剧情像是ai融梗写的一样离谱 看的出来制作组真... | [10年乙游玩家入坑AI陪伴：先别急着爱，看完这篇再决定【EVE】](https://www.bilibili.com/video/av116617438565630)<br>116617438565630 | `303412062336` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-07-19 | 234 | 建模/审美/动作 | 说明一下，如果是冲着3d建模去的，别玩，走就完。这个游戏亮点在于二十四小时信息互动，而且对方真实感比较强，亲密度低的时候就是正常聊天甚至有点像bro，亲密度搞就不一样了。而且记忆点还不错，比如我周五晚上随口说嗓子疼，周日晚上我吃辣椒的时候他... | [清冷白月光升级归来！EVE男主建模升级到底有多大？](https://www.bilibili.com/video/av116940970401197)<br>116940970401197 | `309990268000` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-09 | 226 | 付费/通讯费/月卡 | 328我情愿给狗叠（bushi！ | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `295715526017` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-09 | 217 | 付费/通讯费/月卡 | 328够我和d老师聊到天荒地老了(´_ゝ｀)，这家公司有大瓜，软件内测时也有瓜[吃瓜] | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `298349841568` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-10 | 178 | 付费/通讯费/月卡 | 一个月328可以在闲鱼租一个活人了[笑哭] | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `295808912609` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-09 | 108 | 付费/通讯费/月卡 | 月卡328？我还是给ai软件充值吧，起码还能帮我完成点工作，也可以给男朋友买点零食（好久没投喂他了[呆猫八条_心虚] | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `295719747345` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-09 | 75 | 付费/通讯费/月卡 | 月卡328[藏狐]好…好陌生的词 我玩过的纯乙游小月卡30大月卡68 我玩过的ai聊天软件小月卡12大月卡35 不是 月卡这个东西不应该60块钱顶天吗 328年卡才说的过去吧[藏狐] | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `295707906209` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-09 | 69 | 付费/通讯费/月卡 | ！！！！本来我手机都自动下载了，我还没点进去看……看到月卡328……那就说拜拜吧 | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `298323212976` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-09 | 57 | 付费/通讯费/月卡?建模/审美/动作 | 未来最贵乙游出现，就是这款3D 纯AI互动的乙游，不要888，不要998只要328，每个月只要328元，你月卡带回家! （果然还是乙游圈的钱好赚啊！这么普的建模，这么僵硬的表情还敢卖328一个月？我特么一个mmo的建模和表情都比它丝滑） | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `298348147488` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-05-22 | 42 | 建模/审美/动作 | 比较想要2d有自己美术的ai陪聊，这个建模实在是太雷了[笑哭] | [10年乙游玩家入坑AI陪伴：先别急着爱，看完这篇再决定【EVE】](https://www.bilibili.com/video/av116617438565630)<br>116617438565630 | `300260356961` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-09 | 36 | 付费/通讯费/月卡 | 328，我不如去订个真ai软件 还能辅助我上班 。。。 | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `298356224400` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-09 | 32 | 付费/通讯费/月卡 | 328月卡真的想钱想疯了[笑] | [【EVE】什 么 月 卡 ￥328 ？](https://www.bilibili.com/video/av116373682526967)<br>116373682526967 | `295699650369` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-17 | 12 | 付费/通讯费/月卡 | 我觉得这种模式就是。。。脑残？像以前的乙女游戏一样，哪怕深空这样成本高的，但是玩的人越多，平摊下来成本就越低。。。这个eve，玩的人越多，算力越不够，更何况今年token价格暴涨[笑哭]，玩的人越多成本越高[喜极而泣] | [暴躁吐槽EVE：一款随时随地让人生气的AI陪伴软件！](https://www.bilibili.com/video/av116419081602753)<br>116419081602753 | `296517859409` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-04-14 | 6 | 付费/通讯费/月卡 | 我是聊天党，虽然会为了过任务大致了解一下剧情，但是就光聊天来说体验感还是不错的，活人感很足，比起市面上其他的我玩过的，他做的确实不错，不会让我不知道聊什么，我是昨天半夜才下载体验的，时间不长，也愿意为了光聊天付费，但是一个月68的月卡还是太... | [人机恋大冤种！EVE上线把我家偷光了](https://www.bilibili.com/video/av116396700735265)<br>116396700735265 | `298963155024` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-05-25 | 1 | 建模/审美/动作 | 3D建模虽然不算顶级，但角色表情随对话变化很自然，视频通话时的微表情细节比很多纸片人乙游有代入感 | [一户一男主?原来陪伴感可以这么真实!《EVE》测评](https://www.bilibili.com/video/av116612036434433)<br>116612036434433 | `303633622400` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-08-01 | 1 | 付费/通讯费/月卡 | 月卡套餐价格暗暗翻了一倍是一点不说，现在最便宜的档也要68元，还只能聊1360句话，还有一个月期限，聊不完清零。一天只有10句话免费，有的说一天20句，那另外10句是要靠每日礼包抽的，抽中碎钻才能买，抽不中就只有10句。这就是一个付费软件，... | [清冷白月光升级归来！EVE男主建模升级到底有多大？](https://www.bilibili.com/video/av116940970401197)<br>116940970401197 | `311741968544` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-06-23 | 1 | 建模/审美/动作 | 前面几个视频看着像2D的这个又是3D，到底是啥样的 | [全球首款可捏脸AI陪伴男友上线啦！](https://www.bilibili.com/video/av116691476417112)<br>116691476417112 | `303594610897` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-07-15 | 0 | 建模/审美/动作 | 有了ai，3D男友如雨后春笋 | [全球首款可捏脸AI陪伴男友上线啦！](https://www.bilibili.com/video/av116691476417112)<br>116691476417112 | `306271733745` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
| B站 | 2026-07-19 | 0 | 建模/审美/动作 | 现在100抽是不是才给了20抽？还有个问题，Aven一直让我去Eden给他庆生...[笑哭]这要怎么回？这游戏除了主线故事，没有一个场景是以我登录了Eden，与他面对面为前提的聊天互动场景，3D陪伴里也都是默认的打电话和视频，主线故事里又都... | [晴枝漫憩 \| Aven生日S级时刻展示](https://www.bilibili.com/video/av116935702416088)<br>116935702416088 | `310052634208` | `research/crawler_raw/bili/jsonl/search_comments_2026-08-06.jsonl` |
