-- =====================================================================================
-- aicg 全量表结构（目标态）
-- 依据：aicg.sql（现有 6 表）+《开发标准手册.md》§4 字段字典 / §6.3 契约 C1~C9 +《数据库表文档.md》修改清单 M1~M6
-- 说明：
--   第一部分 = 现有 6 张表的目标态 DDL（已并入 M2/M3/M5 修改，【M*】标记处为相对 aicg.sql 的变化）
--   第二部分 = 阶段二业务表全新建表（14 张，含 C1~C9 契约要求的字段；8b 题材标签为 M7 新增）
--   第三部分 = 数据修改（M1 内置分类 / M4 业务页引导词 / M7 题材标签种子）
--   执行顺序：先第三部分的 M1（技能分类），再第一、二部分建表。
--   与现有库共存时：第一部分只对存量库执行差异 ALTER（见《数据库表文档.md》），全新建库可整文件执行。
-- =====================================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================================
-- 第一部分 现有 6 张表（目标态）
-- =====================================================================================

-- ----------------------------
-- 1. 用户 —— 登录账号表（仅本机管理员，无注册入口）
-- ----------------------------
DROP TABLE IF EXISTS `用户`;
CREATE TABLE `用户`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '用户主键',
  `用户名` varchar(50) NOT NULL COMMENT '登录名，唯一；预置管理员为 zhsw',
  `密码哈希` varchar(128) NOT NULL COMMENT '登录密码哈希（pbkdf2_sha256），不明文存',
  `昵称` varchar(50) NULL DEFAULT NULL COMMENT '界面显示名，可空',
  `启用` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否允许登录：1 允许，0 停用',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '记录创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '记录最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_用户_用户名`(`用户名` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '登录用的账号表；仅本机管理员，无注册入口' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 2. 模型配置 —— 全平台一份模型地址/档位/价目配置（单行表，只更新不删除）
--    【M5 新增】生图/生视频/TTS 模型 + 价目 JSON，对齐 /model-config 页"档位与价目一处改全局生效"
-- ----------------------------
DROP TABLE IF EXISTS `模型配置`;
CREATE TABLE `模型配置`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '配置主键，全表只允许一行',
  `大模型名称` varchar(100) NULL DEFAULT NULL COMMENT '界面展示用的模型称呼',
  `LLM地址` varchar(255) NULL DEFAULT NULL COMMENT '模型配置页填写的 LLM 服务地址（含端口，协议由页面约定，不写死）',
  `LLM密钥` varchar(255) NULL DEFAULT NULL COMMENT 'LLM 接口密钥，本地可空',
  `LLM模型名` varchar(100) NULL DEFAULT NULL COMMENT '请求 LLM 时使用的模型名',
  `ComfyUI地址` varchar(255) NULL DEFAULT NULL COMMENT '模型配置页填写的 ComfyUI 地址',
  `ComfyUI工作流目录` varchar(512) NULL DEFAULT NULL COMMENT 'Comfy 工作流 JSON 所在目录',
  `ComfyUI输出目录` varchar(512) NULL DEFAULT NULL COMMENT 'Comfy 原始输出目录，worker 再拷回 backend/资源/产物/',
  `生图模型` varchar(100) NULL DEFAULT NULL COMMENT '【M5】美术资产生图模型名，如 gpt-image 2；/video/art 页头下拉从这里读',
  `生视频模型` varchar(100) NULL DEFAULT NULL COMMENT '【M5】镜头生成视频模型名；/video/director 生成条从这里读',
  `TTS模型` varchar(100) NULL DEFAULT NULL COMMENT '【M5】音色合成模型名，如 Qwen3 TTS；/video/art 音色区从这里读',
  `价目` json NULL DEFAULT NULL COMMENT '【M5】积分价目表 JSON，如 {"重提取":50,"TTS":10,"生图":10,"生视频":10,"合成":20}；一处改全局生效',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '配置最后更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '全平台一份模型地址/档位/价目配置，最多一行，只更新不删除' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 3. 技能分类 —— 技能分类字典（预置内置分类 + 用户自增）
-- ----------------------------
DROP TABLE IF EXISTS `技能分类`;
CREATE TABLE `技能分类`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '分类主键',
  `名称` varchar(50) NOT NULL COMMENT '分类显示名（技能列表接口按它过滤），如 剧本创作/视频生成/minimax',
  `编码` varchar(50) NOT NULL COMMENT '程序用编码，唯一；用户自增分类由后端自动生成，如 script_writing/video_gen/cat_N',
  `排序` int(11) NOT NULL DEFAULT 0 COMMENT '列表排序，数字越小越靠前',
  `系统内置` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1=预置分类不可删（写作技能/分镜技能/未分类/剧本创作/视频生成）；0=用户自增，无技能引用时可删',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '分类创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_技能分类_编码`(`编码` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '技能的分类字典；内置分类见第三部分 M1 数据' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 4. 技能 —— 上传/导入的技能包（一行 = backend/资源/技能/ 下一个目录，删行联动删磁盘）
-- ----------------------------
DROP TABLE IF EXISTS `技能`;
CREATE TABLE `技能`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '技能主键',
  `目录名` varchar(255) NOT NULL COMMENT '解压后在 backend/资源/技能/ 下的目录名，不是绝对路径；唯一',
  `名称` varchar(255) NOT NULL COMMENT '技能显示名称',
  `简介` text NULL COMMENT '技能说明，上传后可由模型识别再人工改',
  `分类id` bigint(20) NOT NULL COMMENT '所属分类；必须指向某分类行（含「未分类」）。RESTRICT 外键：分类下有技能时禁止删分类',
  `来源` varchar(50) NOT NULL DEFAULT '上传压缩包' COMMENT '来源：上传压缩包 / 本地导入（后端已放开本地导入）',
  `原压缩包名` varchar(255) NULL DEFAULT NULL COMMENT '用户上传时的 zip 等文件名或本地导入的仓库路径，便于对照',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '技能创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '技能最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_技能_目录名`(`目录名` ASC) USING BTREE,
  INDEX `idx_技能_分类id`(`分类id` ASC) USING BTREE,
  CONSTRAINT `fk_技能_分类id` FOREIGN KEY (`分类id`) REFERENCES `技能分类` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户上传/导入的技能包；删表行同时删磁盘目录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 5. 提示词模板 —— 按 类型 字符串寻址的页面引导词（弹窗"恢复本页默认"的数据源）
-- ----------------------------
DROP TABLE IF EXISTS `提示词模板`;
CREATE TABLE `提示词模板`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '提示词模板主键',
  `类型` varchar(50) NOT NULL COMMENT '寻址键，约定 扩写:<路由> / 生成:<路由>，如 扩写:/test/d1-t2v、生成:/video/assets',
  `系统提示词` text NULL COMMENT '该类型使用的完整系统提示词',
  `生成提示词` text NULL COMMENT '该类型使用的完整生成提示词（技能弹窗默认引导词）',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '记录创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '记录最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_提示词模板_类型`(`类型` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '按类型存放系统提示词与生成提示词；测试台=扩写:<路由>，业务页=生成:<路由>（见 M4）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 6. task —— 所有测试/生成任务的唯一管理表（56+7 列宽表）
--    【M2 新增 6 列】request_id/进度/积分/重试次数/页面来源/业务实体（对齐契约 C5/C8/C9）
--    【M3 修改】类型 列注释补全为后端白名单 23 种
--    组1~4提示词+组1~4时长 正好承载单镜四宫格
-- ----------------------------
DROP TABLE IF EXISTS `task`;
CREATE TABLE `task`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '任务主键，前端轮询、取消、日志弹窗都用这个 id',
  `request_id` varchar(64) NULL DEFAULT NULL COMMENT '【M2】幂等键：同 创建人id+request_id 重复提交返回原任务（uk_task_幂等）；存量任务可空',
  `类型` varchar(50) NOT NULL COMMENT '【M3】任务种类，后端白名单 23 种：文本回复/图片解析/文生图/生成图片/编辑图片单图/编辑图片三图/三图编辑一致版/多图编辑多人合并版/文生图8K/动漫转真人/首尾帧/文生视频/参考生视频/多参考生视频/首尾帧生视频/加速版生视频/外部分组图生视频/外部分组多参考生视频/二采重绘/二采加速生视频/去水印/资产提取/分镜拆分',
  `状态` varchar(20) NOT NULL DEFAULT '已创建' COMMENT '执行状态：已创建/已提交/排队中/生成中/成功/失败/中断/已取消',
  `进度` tinyint(4) NULL DEFAULT NULL COMMENT '【M2】执行进度 0~100；NULL=该类型不支持进度',
  `积分` decimal(10, 2) NULL DEFAULT NULL COMMENT '【M2】本任务积分消耗；提交预扣→成功落账/失败回退（流水见 积分流水 表）；NULL=免费',
  `重试次数` int(11) NOT NULL DEFAULT 0 COMMENT '【M2】失败自动重试次数，上限 3（指数退避）',
  `创建人id` bigint(20) NOT NULL COMMENT '提交该任务的用户',
  `页面来源` varchar(64) NULL DEFAULT NULL COMMENT '【M2】提交页面路由，如 /video/shot；按页聚合统计与权限校验',
  `业务实体` varchar(128) NULL DEFAULT NULL COMMENT '【M2】关联业务实体，任务完成据此回写业务状态（契约 C5），如 1:1:SH002（剧:集:镜）或 CHAR_001（资产id）',
  `comfy_prompt_id` varchar(64) NULL DEFAULT NULL COMMENT '提交到 Comfy 成功后返回的 prompt_id；LLM 测试为空',
  `日志路径` varchar(512) NULL DEFAULT NULL COMMENT '相对 backend/资源/日志/ 的日志文件路径，日志弹窗按任务 id 读',
  `正向提示词` text NULL COMMENT '前端提交、前端展示、实际发给模型的完整正向提示词，后端禁止再拼接后覆盖',
  `反向提示词` text NULL COMMENT '前端提交的完整反向提示词；LLM 无反向可空',
  `图片宽` int(11) NULL DEFAULT NULL COMMENT '出图像素宽度；非出图任务可空',
  `图片高` int(11) NULL DEFAULT NULL COMMENT '出图像素高度；非出图任务可空',
  `视频宽` int(11) NULL DEFAULT NULL COMMENT '视频像素宽度；非视频任务可空',
  `视频高` int(11) NULL DEFAULT NULL COMMENT '视频像素高度；非视频任务可空',
  `一采MP` decimal(6, 2) NULL DEFAULT NULL COMMENT '视频采样分辨率（兆像素）。非二采视频任务只填这一列；二采任务填一采档；非视频任务可空',
  `二采MP` decimal(6, 2) NULL DEFAULT NULL COMMENT '二采档采样分辨率（兆像素）。仅二采任务填写，其它任务必须空；禁止一列兼存两个 MP',
  `cfg` decimal(6, 2) NULL DEFAULT NULL COMMENT 'MiniMax H3 Director 的 cfg 值；仅导演台系列工作流填写',
  `seed` bigint(20) NULL DEFAULT NULL COMMENT '随机种子',
  `水印` varchar(50) NULL DEFAULT NULL COMMENT '去水印测试的水印类型或标识；非去水印任务可空',
  `系统提示词` text NULL COMMENT 'LLM 文本/识图测试的完整系统提示词，前端提交完整、后端禁止拼接；Comfy 任务可空',
  `组1提示词` text NULL COMMENT '外部分组第1组提示词（业务语义：单镜四宫格第1格）',
  `组2提示词` text NULL COMMENT '外部分组第2组提示词（单镜四宫格第2格）',
  `组3提示词` text NULL COMMENT '外部分组第3组提示词（单镜四宫格第3格）',
  `组4提示词` text NULL COMMENT '外部分组第4组提示词（单镜四宫格第4格）',
  `组1时长` decimal(10, 2) NULL DEFAULT NULL COMMENT '外部分组第1组秒数',
  `组2时长` decimal(10, 2) NULL DEFAULT NULL COMMENT '外部分组第2组秒数',
  `组3时长` decimal(10, 2) NULL DEFAULT NULL COMMENT '外部分组第3组秒数',
  `组4时长` decimal(10, 2) NULL DEFAULT NULL COMMENT '外部分组第4组秒数',
  `输入图1` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片1，相对 backend/资源/上传/；最多 9 张',
  `输入图2` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片2',
  `输入图3` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片3',
  `输入图4` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片4',
  `输入图5` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片5',
  `输入图6` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片6',
  `输入图7` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片7',
  `输入图8` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片8',
  `输入图9` varchar(512) NULL DEFAULT NULL COMMENT '输入/参考图片9',
  `输入视频1` varchar(512) NULL DEFAULT NULL COMMENT '输入视频1，相对 backend/资源/上传/；最多 3 个',
  `输入视频2` varchar(512) NULL DEFAULT NULL COMMENT '输入视频2',
  `输入视频3` varchar(512) NULL DEFAULT NULL COMMENT '输入视频3',
  `输入音频1` varchar(512) NULL DEFAULT NULL COMMENT '输入音频1，相对 backend/资源/上传/；最多 3 个',
  `输入音频2` varchar(512) NULL DEFAULT NULL COMMENT '输入音频2',
  `输入音频3` varchar(512) NULL DEFAULT NULL COMMENT '输入音频3',
  `回复` text NULL COMMENT 'LLM 返回正文；Comfy 任务为空',
  `产物图片` varchar(512) NULL DEFAULT NULL COMMENT '成功时产出的图片路径，相对 backend/资源/产物/；最多 1 张，禁止与产物视频同时有值',
  `产物视频1` varchar(512) NULL DEFAULT NULL COMMENT '成功时产出的第 1 个视频路径；与产物图片互斥',
  `产物视频2` varchar(512) NULL DEFAULT NULL COMMENT '成功时产出的第 2 个视频路径；仅一次返 2 个视频的任务填',
  `错误信息` text NULL COMMENT '失败、中断或取消时的异常信息（上线前改错误码脱敏，见手册 §9.4）',
  `错误文件` varchar(512) NULL DEFAULT NULL COMMENT '失败时出错的 py 文件真实路径（仅内网开发期直传）',
  `错误行号` int(11) NULL DEFAULT NULL COMMENT '失败时出错的行号（仅内网开发期直传）',
  `错误函数` varchar(100) NULL DEFAULT NULL COMMENT '失败时出错的函数名（仅内网开发期直传）',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '任务在本平台创建的时间',
  `开始时间` datetime(6) NULL DEFAULT NULL COMMENT 'ComfyUI 真正开始跑该任务的时间；排队中必须为空',
  `结束时间` datetime(6) NULL DEFAULT NULL COMMENT '进入成功、失败、中断或已取消的时间',
  `比例` varchar(16) NULL DEFAULT NULL COMMENT '视频宽高比标签键（16:9/9:16 等），仅参考生视频填写；非视频任务可空',
  `视频时长` decimal(6, 2) NULL DEFAULT NULL COMMENT '请求的视频生成时长（秒）；参考生视频默认 5，二采默认 7；非视频任务可空',
  `产物图片2` varchar(512) NULL DEFAULT NULL COMMENT '成功时产出的第 2 张图片路径；目前仅文生图8K 使用（1x 原图 + 4x 放大）',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_task_幂等`(`创建人id` ASC, `request_id` ASC) USING BTREE COMMENT '【M2】同用户同 request_id 唯一，实现提交幂等',
  INDEX `idx_task_状态`(`状态` ASC) USING BTREE,
  INDEX `idx_task_创建人id`(`创建人id` ASC) USING BTREE,
  INDEX `idx_task_类型`(`类型` ASC) USING BTREE,
  INDEX `idx_task_创建时间`(`创建时间` ASC) USING BTREE,
  INDEX `idx_task_页面来源`(`页面来源` ASC) USING BTREE,
  INDEX `idx_task_业务实体`(`业务实体` ASC) USING BTREE,
  CONSTRAINT `fk_task_创建人id` FOREIGN KEY (`创建人id`) REFERENCES `用户` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '所有测试/生成任务唯一管理表（业务 AI 动作也走本表）；任意时刻最多一条 Comfy 任务处于生成中' ROW_FORMAT = Dynamic;

-- =====================================================================================
-- 第二部分 阶段二业务表（13 张，全新建）
--   引用链：剧 1→N 分集；分集 1→1 剧本；剧本 →提取→ 资产[]；资产 →生成→ 美术定装；
--           剧本+资产 →拆分→ 分镜[]；分镜 1→1 镜头脚本 + N 镜头视频；镜头视频[] →合成→ 成片
--   命名沿用库内中文表名约定；json 列存结构化产物，schema 不随内容膨胀
-- =====================================================================================

-- ----------------------------
-- 7. 剧 —— P0 立项记录（/script 与 /video 两处列表同源）
-- ----------------------------
DROP TABLE IF EXISTS `剧`;
CREATE TABLE `剧`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '剧主键',
  `用户id` bigint(20) NOT NULL COMMENT '归属用户；列表按此隔离防越权（手册 §9.3）',
  `剧名` varchar(100) NOT NULL COMMENT '剧名，全局唯一（/script/new 提交时后端查重）',
  `集数` int(11) NOT NULL COMMENT '总集数，2~100',
  `题材` varchar(50) NOT NULL COMMENT '题材，决定技能产出语域，如 玄幻/都市',
  `创意` text NOT NULL COMMENT '一句创意，P1 方案生成的种子（≥20 字才允许生成方案）',
  `起点方式` varchar(20) NOT NULL DEFAULT '原创' COMMENT '故事起点：原创/模板/灵感启发',
  `创作进度` tinyint(4) NOT NULL DEFAULT 0 COMMENT '创作线进度 0~100（/script 列表卡显示）',
  `视频进度` tinyint(4) NOT NULL DEFAULT 0 COMMENT '视频线进度 0~100（/video 列表卡显示，按各集成片状态聚合）',
  `封面图片` varchar(512) NULL DEFAULT NULL COMMENT '剧封面图路径，相对 backend/资源/上传/；空=显示占位图；/script 与 /video 列表卡共用',
  `保存地址` varchar(512) NULL DEFAULT NULL COMMENT '剧工程/产物保存目录（本机或网盘路径），可空；列表卡悬浮提示展示',
  `状态` varchar(20) NOT NULL DEFAULT '草稿' COMMENT '创作状态：草稿(刚立项未出方案)/创作中(方案或剧本进行中)/已完成(全剧剧本定稿)；由各步骤回写',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_剧_剧名`(`剧名` ASC) USING BTREE,
  INDEX `idx_剧_用户id`(`用户id` ASC) USING BTREE,
  CONSTRAINT `fk_剧_用户id` FOREIGN KEY (`用户id`) REFERENCES `用户` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '短剧立项记录；/script 与 /video 两大模块共同的数据骨架' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 8. 方案 —— 创作方案（五分区：时空背景/故事线/爽点矩阵/商业卖点/结局设计）
--    C9：分区级 PATCH + baseVersion 乐观锁（冲突 409）
-- ----------------------------
DROP TABLE IF EXISTS `方案`;
CREATE TABLE `方案`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '方案主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧；一剧多候选方案',
  `版本号` varchar(50) NOT NULL DEFAULT '方案一' COMMENT '方案版本名，如 方案一/方案二',
  `是否选定` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1=当前选定方案；选定后才能进方案详情与后续步骤。同剧仅一行=1',
  `候选卡` json NULL COMMENT '【M7】/script/plan 方案卡七字段：{标题,故事线,题材,基调,结局,驱动,风险}；AI 生成/手改/选定都写这里',
  `时空背景` json NULL COMMENT '五分区之一：{时空锚,硬规则[],禁忌口径[],场景库[{名称,功能,视觉,预算档}],场景预算}；场景库是视频线资产提取的场景种子',
  `故事线` json NULL COMMENT '五分区之二：核心冲突键值段',
  `爽点矩阵` json NULL COMMENT '五分区之三：[{集段,类型,设计,强度}]',
  `商业卖点` json NULL COMMENT '五分区之四：{爽点兑现[],反派压力[]}（观众买单理由/付费卡点版本已删）',
  `结局设计` json NULL COMMENT '五分区之五：键值段',
  `基础版本` int(11) NOT NULL DEFAULT 1 COMMENT '【C9】乐观锁版本号：编辑请求带 baseVersion，不匹配返回 409',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_方案_剧id`(`剧id` ASC) USING BTREE,
  CONSTRAINT `fk_方案_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '创作方案（全剧宪法）；每次分区级保存写一条 方案历史 快照可回滚' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 8b. 题材标签 —— 题材标签库（【M7】2026-10-29 新增；/script/new 题材 chips 数据源）
-- ----------------------------
DROP TABLE IF EXISTS `题材标签`;
CREATE TABLE `题材标签`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `名称` varchar(50) NOT NULL COMMENT '标签名，全局唯一',
  `系统内置` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1=内置标签（M7 种子写入 16 个），页面不提供删除',
  `排序` int(11) NOT NULL DEFAULT 0 COMMENT '显示顺序，小在前',
  `用户id` bigint(20) NULL COMMENT '添加人；内置为 NULL',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_题材标签_名称`(`名称` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '题材标签库：/script/new 题材 chips 数据源，手动添加也写这里（最多 2 个：主+辅）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 9. 方案历史 —— 方案每次保存的快照（分区级回滚依据）
-- ----------------------------
DROP TABLE IF EXISTS `方案历史`;
CREATE TABLE `方案历史`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '历史主键',
  `方案id` bigint(20) NOT NULL COMMENT '所属方案',
  `分区键` varchar(20) NOT NULL COMMENT '被保存的分区：时空背景/故事线/爽点矩阵/商业卖点/结局设计',
  `快照` json NOT NULL COMMENT '该分区保存时刻的完整 JSON 快照',
  `来源` varchar(20) NOT NULL DEFAULT '人工编辑' COMMENT '本次变更来源：人工编辑/AI生成',
  `操作人id` bigint(20) NOT NULL COMMENT '操作用户',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '快照时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_方案历史_方案id`(`方案id` ASC, `分区键` ASC) USING BTREE,
  CONSTRAINT `fk_方案历史_方案id` FOREIGN KEY (`方案id`) REFERENCES `方案` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_方案历史_操作人id` FOREIGN KEY (`操作人id`) REFERENCES `用户` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '方案分区保存快照，支持回滚' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 10. 人物 —— 人物卡（资产清单与音色的种子）
-- ----------------------------
DROP TABLE IF EXISTS `人物`;
CREATE TABLE `人物`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `人物id` varchar(32) NOT NULL COMMENT '业务编号 CHAR_xxx，剧内唯一；/video/assets 人物分区按它对账',
  `名` varchar(50) NOT NULL COMMENT '人物名',
  `别名` json NULL COMMENT '别名数组，如 ["三班教室","教室"]',
  `性别` varchar(10) NOT NULL DEFAULT '男' COMMENT '男/女',
  `年龄档` varchar(20) NULL DEFAULT NULL COMMENT '年龄档，如 青年/儿童/老年',
  `外观全文` text NULL COMMENT '可拍级外观描述（资产提取的原文来源）',
  `性格` text NULL COMMENT '性格要点',
  `关系` text NULL COMMENT '人物关系（本剧关系：主角/反派/核心成员…）',
  `简介` varchar(255) NULL COMMENT '一句话简介（卡片副题）【2026-11-02】',
  `分组` varchar(50) NULL DEFAULT '本剧角色' COMMENT '卡片分组【2026-11-02】',
  `卡色` varchar(10) NULL COMMENT '卡片配色，如 #3b4a63【2026-11-02】',
  `身份` text NULL COMMENT '身份（可分段：第1-5集：…；第6集起：…）【2026-11-02】',
  `关系变化` text NULL COMMENT '与主角关系随集变化（可分段）【2026-11-02】',
  `态度` text NULL COMMENT '立场态度（可分段）【2026-11-02】',
  `外貌` text NULL COMMENT '外貌，能直接拿去画（可分段）【2026-11-02】',
  `身材` varchar(255) NULL COMMENT '身材【2026-11-02】',
  `穿搭` text NULL COMMENT '穿搭（可分段）【2026-11-02】',
  `身体情况` text NULL COMMENT '身体情况（可分段）【2026-11-02】',
  `情感情况` text NULL COMMENT '情感情况（可分段）【2026-11-02】',
  `精神情况` text NULL COMMENT '精神情况（可分段）【2026-11-02】',
  `当前状态` text NULL COMMENT '当前状态（可分段）【2026-11-02】',
  `当前姿势` varchar(255) NULL COMMENT '当前姿势（可分段）【2026-11-02】',
  `内心想法` text NULL COMMENT '内心想法（可分段）【2026-11-02】',
  `技能` text NULL COMMENT '角色技能（可分段）【2026-11-02】',
  `核心目标` text NULL COMMENT '核心目标（可分段）【2026-11-02】',
  `关系网` text NULL COMMENT '和谁是什么关系的概述【2026-11-02】',
  `背景故事` text NULL COMMENT '背景故事【2026-11-02】',
  `台词风格` varchar(255) NULL COMMENT '台词风格【2026-11-02】',
  `口头禅` varchar(255) NULL COMMENT '口头禅【2026-11-02】',
  `概括` varchar(500) NULL COMMENT '人物概括（下游页面浓缩版）【2026-11-02】',
  `音色提示词` text NULL COMMENT '音色提示词，格式「性别，年龄档，音色 · 年龄，身份一句话」；非空校验（C3 音色前置的种子）',
  `基础版本` int(11) NOT NULL DEFAULT 1 COMMENT '【C9】乐观锁版本号',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_人物_剧内编号`(`剧id` ASC, `人物id` ASC) USING BTREE,
  CONSTRAINT `fk_人物_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '人物卡：外观/性格/关系/音色提示词' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 11. 分集 —— 分集目录（每集梗概+钩子）
-- ----------------------------
DROP TABLE IF EXISTS `分集`;
CREATE TABLE `分集`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `集号` int(11) NOT NULL COMMENT '集号，剧内连续唯一',
  `标题` varchar(100) NULL DEFAULT NULL COMMENT '集标题，如 回到讲台',
  `梗概` varchar(500) NOT NULL COMMENT '本集梗概（80~120 字）；非空才能标已定稿',
  `钩子` varchar(500) NULL DEFAULT NULL COMMENT '结尾钩子：制造"下一集必须看"的缺口',
  `状态` varchar(10) NOT NULL DEFAULT '未写' COMMENT '未写/已写/已定稿',
  `幕` varchar(50) NULL DEFAULT NULL COMMENT '所属幕：第一幕 · 建置 / 第二幕 · 对抗 / 第三幕 · 收束',
  `关键` tinyint(1) NOT NULL DEFAULT 0 COMMENT '关键集标记',
  `卡点` tinyint(1) NOT NULL DEFAULT 0 COMMENT '付费卡点集标记',
  `情绪分` int(11) NULL DEFAULT NULL COMMENT '情绪强度1-5，节奏折线用',
  `字数` int(11) NOT NULL DEFAULT 0 COMMENT '本集预估/实际字数（7.4定义过，建表漏建，此处补上）',
  `目标` int(11) NOT NULL DEFAULT 3000 COMMENT '目标字数',
  `尾钩` varchar(500) NULL DEFAULT NULL COMMENT '本集结尾钩子',
  `中心句` varchar(255) NULL DEFAULT NULL COMMENT '本集中心句',
  `出场` text NULL COMMENT '出场人物，顿号分隔',
  `点位` text NULL COMMENT '钩子点位，换行分隔，每行 类型|点|内容',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_分集_剧内集号`(`剧id` ASC, `集号` ASC) USING BTREE,
  CONSTRAINT `fk_分集_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '分集目录：每集一句话梗概+钩子+状态' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 12. 剧本 —— 每集场次化正文（全链路唯一剧本事实源）
--    C1 定稿锁：定稿版 = 视频线资产提取/拆分/单镜的总开关
-- ----------------------------
DROP TABLE IF EXISTS `剧本`;
CREATE TABLE `剧本`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `集号` int(11) NOT NULL COMMENT '集号',
  `版本类型` varchar(10) NOT NULL DEFAULT '创作版' COMMENT '创作版（创作线可改）/ 定稿版（视频线引用快照，C1）',
  `版本` int(11) NOT NULL DEFAULT 1 COMMENT '同版本类型内的版本号，支持回到创作版重改',
  `标题` varchar(100) NULL DEFAULT NULL COMMENT '集标题',
  `总字数` int(11) NOT NULL DEFAULT 0 COMMENT '总字数；定稿前校验单集 800~5000 字',
  `场次` longtext NULL DEFAULT NULL COMMENT '【已弃用】场次数组JSON（旧设计），2026-11-02 起新数据走 场次 实体表（docs 02 第 12 节）',
  `正文` text NULL COMMENT '本集正文全文，按场次排，换行分段',
  `能力档案` text NULL COMMENT '「键：值」行文本（所属势力…目前目标 10 键）',
  `世界状态` text NULL COMMENT '「键：值」行文本（当前世界…附近动向 11 键）',
  `关系网络` text NULL COMMENT '「键：值」行文本（当前主线/预告1/预告2/蝴蝶效应/历史进程/角色记录）',
  `记忆回廊` text NULL COMMENT '「键：值」行文本（长期记忆+短期记忆1-6）',
  `行动推荐` text NULL COMMENT '行文本，每行「N. 内容」',
  `状态` varchar(16) NULL DEFAULT '待复核' COMMENT '待复核/已复核（页面复核语义）',
  `定稿` tinyint(1) NOT NULL DEFAULT 0 COMMENT '【C1】1=已定稿锁定；解锁需确认且资产/分镜页提示"剧本已变动建议重提取/重拆"',
  `定稿时间` datetime(6) NULL DEFAULT NULL COMMENT '定稿时间',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_剧本_剧集版本`(`剧id` ASC, `集号` ASC, `版本类型` ASC, `版本` ASC) USING BTREE,
  CONSTRAINT `fk_剧本_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '每集剧本（创作版/定稿版分离+版本链）；定稿版是视频线的唯一事实源' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 13. 资产 —— 从本集剧本提取的可拍资产（人物/场景/道具/服装四分区）
--    2026-11-02 用户授权改表：名→名称、本集关系→关系、AI摘要→摘要、别名 json→varchar(300)，
--    去掉 手改摘要/手改字段/连续性/基础版本（新接口不做手改分层与乐观锁），加 排序
-- ----------------------------
DROP TABLE IF EXISTS `资产`;
CREATE TABLE `资产`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `集号` int(11) NOT NULL COMMENT '所属集',
  `资产id` varchar(32) NOT NULL COMMENT '业务编号：CHAR_xxx/SCN_xxx/PROP_xxx/COST_xxx，剧内集内唯一',
  `类型` varchar(10) NOT NULL COMMENT '人物/场景/道具/服装',
  `名称` varchar(100) NOT NULL COMMENT '资产名',
  `别名` varchar(300) NULL DEFAULT NULL COMMENT '顿号分隔的别名文本',
  `关系` varchar(10) NOT NULL DEFAULT '新增' COMMENT '新增/引用',
  `级别` varchar(50) NULL DEFAULT NULL COMMENT '主角/次主场景/关键道具 等',
  `摘要` text NULL COMMENT '可拍细节摘要（外观/物件/状态）',
  `排序` int(11) NOT NULL DEFAULT 0 COMMENT '列表顺序',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_资产_剧集编号`(`剧id` ASC, `集号` ASC, `资产id` ASC) USING BTREE,
  INDEX `idx_资产_类型`(`剧id` ASC, `集号` ASC, `类型` ASC) USING BTREE,
  CONSTRAINT `fk_资产_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '可拍资产四分区（每集 25 项量级）；2026-11-02 改表对齐新接口' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 14. 美术定装 —— 每个资产的出图提示词+必须保持/禁止出现+音色
--    2026-11-02 用户授权重构：去掉 6 个 json 列（参考图/参考图历史/AI必须保持/手改必须保持/
--    AI禁止出现/手改禁止出现）与 基础版本 乐观锁；必须保持/禁止出现 改换行分隔文本列，
--    新增 生图提示词；参考图拆独立表 参考图（一图一行带标注，见 14.1）
-- ----------------------------
DROP TABLE IF EXISTS `美术定装`;
CREATE TABLE `美术定装`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `资产行id` bigint(20) NOT NULL COMMENT '所属 资产.id（一资产一定装行）',
  `全局风格` varchar(100) NULL DEFAULT NULL COMMENT '提取风格，如 校园青春日系胶片风',
  `画幅` varchar(20) NOT NULL DEFAULT '9:16' COMMENT '画幅，默认 9:16 竖屏',
  `分辨率` varchar(20) NOT NULL DEFAULT '480p' COMMENT '参考图分辨率档',
  `生图提示词` text NULL COMMENT '出图正向提示词（编辑提示词的载体），参考图按它生成',
  `必须保持` text NULL COMMENT '必须保持的视觉特征，多条换行分隔',
  `禁止出现` text NULL COMMENT '禁止出现的元素，多条换行分隔',
  `生图状态` varchar(10) NOT NULL DEFAULT '待生成' COMMENT '待生成/生成中/已生成',
  `音色提示词` text NULL COMMENT '人物音色提示词（仅人物资产有值）',
  `音色名` varchar(100) NULL DEFAULT NULL COMMENT '选中的音色库名（如 沈砚），选择后与音色url 成对落库',
  `音色url` varchar(512) NULL DEFAULT NULL COMMENT '已合成音色文件相对路径；【C3】台词镜头生成视频前必须非空',
  `音色模型` varchar(100) NULL DEFAULT NULL COMMENT 'TTS 模型名',
  `音色积分` decimal(10, 2) NULL DEFAULT NULL COMMENT '本次音色合成消耗积分',
  `音色状态` varchar(10) NOT NULL DEFAULT '待生成' COMMENT '待生成/生成中/已生成',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_美术定装_资产行`(`资产行id` ASC) USING BTREE,
  CONSTRAINT `fk_美术定装_资产行id` FOREIGN KEY (`资产行id`) REFERENCES `资产` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '美术定装：出图提示词+必须保持/禁止出现+音色；参考图见 参考图 表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 14.1 参考图 —— 美术定装的参考图（2026-11-02 新建，一图一行带标注；同日加 提示词/分类/形态，见 docs/02 第 14.4 节）
--    一个资产可有多张当前参考图（每张带各自标注/提示词）；重新生成后旧图状态转 历史；
--    来源=生成（AI 出图）/上传（用户上传），跨集美术资产在 /video/art 按资产聚合共同显示；
--    分类=这张图是 人物/场景/道具/服装（默认继承父资产类型）；形态=同一资产的不同服装/状态标签
-- ----------------------------
DROP TABLE IF EXISTS `参考图`;
CREATE TABLE `参考图`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `资产行id` bigint(20) NOT NULL COMMENT '所属 美术定装.id',
  `url` varchar(512) NOT NULL COMMENT '图片相对路径，如 上传/xxx.png',
  `标注` varchar(200) NULL DEFAULT NULL COMMENT '图片标注，如 正面定装/侧面/Q版',
  `提示词` text NULL COMMENT '这张图自己的出图/编辑提示词说明（T2 图片解析自动回写）',
  `分类` varchar(10) NULL DEFAULT NULL COMMENT '图片分类：人物/场景/道具/服装，默认继承父资产类型',
  `形态` varchar(50) NULL DEFAULT NULL COMMENT '形态标签：同一资产的不同服装/状态，如 常服/受伤，空=通用',
  `关联人物` varchar(50) NULL DEFAULT NULL COMMENT '关联人物id：人物类型图关联到哪个角色档案（空=按资产id自动匹配）',
  `来源` varchar(10) NOT NULL DEFAULT '生成' COMMENT '生成/上传',
  `状态` varchar(10) NOT NULL DEFAULT '当前' COMMENT '当前/历史（重新生成后旧图转历史）',
  `排序` int(11) NOT NULL DEFAULT 0 COMMENT '显示顺序',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_参考图_定装`(`资产行id` ASC, `状态` ASC) USING BTREE,
  CONSTRAINT `fk_参考图_资产行id` FOREIGN KEY (`资产行id`) REFERENCES `美术定装` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '参考图：一图一行带标注/提示词/分类/形态（当前/历史），替代 json 数组' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 15. 分镜 —— 本集剧本拆出的镜头行（/video/shot 列表）
--    2026-11-02 用户授权改表：时长 decimal→varchar(16)（存"3s"样文本）、去掉 时长档/拆分版本、
--    景别改可空、视频状态加宽到 16、加 排序；保留 首帧url/尾帧url 供视频生成线使用
-- ----------------------------
DROP TABLE IF EXISTS `分镜`;
CREATE TABLE `分镜`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `集号` int(11) NOT NULL COMMENT '所属集',
  `镜号` varchar(20) NOT NULL COMMENT '镜号，如 SH001，剧内集内唯一',
  `场次` varchar(100) NOT NULL DEFAULT '' COMMENT '所属场次，如 场次 1 · 教室',
  `景别` varchar(20) NULL DEFAULT NULL COMMENT '特写/近景/中景/全景 等',
  `运镜` varchar(50) NULL DEFAULT NULL COMMENT '运镜描述，如 固定/缓推/横移/跟拍',
  `画面` text NOT NULL COMMENT '画面描述',
  `台词` text NULL COMMENT '本镜台词，无台词留空',
  `时长` varchar(16) NULL DEFAULT NULL COMMENT '单镜时长，如 3s',
  `首帧url` varchar(512) NULL DEFAULT NULL COMMENT '首帧参考图（视频生成线预留）',
  `尾帧url` varchar(512) NULL DEFAULT NULL COMMENT '尾帧参考图（视频生成线预留）',
  `视频状态` varchar(16) NOT NULL DEFAULT '待生成' COMMENT '待生成/生成中/已生成',
  `排序` int(11) NOT NULL DEFAULT 0 COMMENT '镜头顺序',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_分镜_剧集镜号`(`剧id` ASC, `集号` ASC, `镜号` ASC) USING BTREE,
  INDEX `idx_分镜_视频状态`(`剧id` ASC, `集号` ASC, `视频状态` ASC) USING BTREE,
  CONSTRAINT `fk_分镜_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '分镜行：场次/景别/运镜/画面/台词/时长/视频状态；2026-11-02 改表对齐新接口' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 16. 镜头脚本 —— 单镜页可编辑终版（/video/director 的 12 字段结构化表单）
--    C2：AI 重写先 diff 预览再覆盖；C9 乐观锁
-- ----------------------------
DROP TABLE IF EXISTS `镜头脚本`;
CREATE TABLE `镜头脚本`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `分镜行id` bigint(20) NOT NULL COMMENT '所属 分镜.id（一镜一脚本）',
  `场次` varchar(100) NOT NULL COMMENT '场次',
  `景别` varchar(20) NOT NULL COMMENT '景别',
  `运镜` varchar(50) NULL DEFAULT NULL COMMENT '运镜',
  `秒` decimal(6, 2) NOT NULL COMMENT '时长（秒）',
  `台词` text NULL COMMENT '台词',
  `画面` text NOT NULL COMMENT '画面描述',
  `时间线` text NULL COMMENT '镜头内部时间线',
  `光线` varchar(200) NULL DEFAULT NULL COMMENT '光线描述',
  `道具` text NULL COMMENT '道具提示',
  `入点` varchar(200) NULL DEFAULT NULL COMMENT '入点描述',
  `出点` varchar(200) NULL DEFAULT NULL COMMENT '出点描述',
  `负面提示` text NULL COMMENT '负面提示（保留 禁止出现 句式）',
  `来源` varchar(10) NOT NULL DEFAULT 'AI' COMMENT '最近一次写入来源：AI/人工',
  `基础版本` int(11) NOT NULL DEFAULT 1 COMMENT '【C9】乐观锁版本号',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_镜头脚本_分镜行`(`分镜行id` ASC) USING BTREE,
  CONSTRAINT `fk_镜头脚本_分镜行id` FOREIGN KEY (`分镜行id`) REFERENCES `分镜` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '单镜结构化脚本终版（12 字段）；AI 重写走 diff 预览（C2）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 17. 镜头视频 —— 镜头生成产物（一镜可多次生成，取最新为生效）
--    关联 task 表；C3 音色前置在提交前校验
-- ----------------------------
DROP TABLE IF EXISTS `镜头视频`;
CREATE TABLE `镜头视频`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `分镜行id` bigint(20) NOT NULL COMMENT '所属 分镜.id',
  `task_id` bigint(20) NOT NULL COMMENT '生成任务（task.id），轮询进度/取消/日志由此寻址',
  `视频url` varchar(512) NULL DEFAULT NULL COMMENT '生成的视频文件路径，相对 backend/资源/产物/；成功后回填',
  `模型` varchar(100) NULL DEFAULT NULL COMMENT '生视频模型名（模型配置.生视频模型快照）',
  `积分` decimal(10, 2) NULL DEFAULT NULL COMMENT '本次生成消耗积分（与 task.积分/积分流水 对账）',
  `时长` decimal(6, 2) NULL DEFAULT NULL COMMENT '成片秒数',
  `状态` varchar(10) NOT NULL DEFAULT '生成中' COMMENT '生成中/成功/失败',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '提交时间',
  `完成时间` datetime(6) NULL DEFAULT NULL COMMENT '完成时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_镜头视频_分镜行id`(`分镜行id` ASC) USING BTREE,
  INDEX `idx_镜头视频_task`(`task_id` ASC) USING BTREE,
  CONSTRAINT `fk_镜头视频_分镜行id` FOREIGN KEY (`分镜行id`) REFERENCES `分镜` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_镜头视频_task` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '镜头视频生成记录；成功后回写 分镜.视频状态（C5）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 18. 成片 —— 每集合成产物（时间线+音轨+字幕+导出）
--    C7：导出强制 AIGC 标识（显式+隐式）
-- ----------------------------
DROP TABLE IF EXISTS `成片`;
CREATE TABLE `成片`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `集号` int(11) NOT NULL COMMENT '所属集；一集多版本成片',
  `版本` int(11) NOT NULL DEFAULT 1 COMMENT '成片版本号',
  `片段序列` json NOT NULL COMMENT '时间线：[{镜号,入点,出点,顺序}]（已生成镜头按序串联）',
  `音轨` json NULL COMMENT '音轨配置：[{类型(配音/BGM/环境音),来源,镜号或全片,音量}]；台词镜头自动配音色（C3）',
  `字幕` json NULL COMMENT '字幕轨：[{镜号,开始,结束,文本}]',
  `总时长` decimal(8, 2) NOT NULL DEFAULT 0 COMMENT '成片总秒数；与剧本目标差 ±20% 时导出前警告',
  `分辨率` varchar(20) NOT NULL DEFAULT '480p' COMMENT '导出分辨率档',
  `码率` varchar(20) NULL DEFAULT NULL COMMENT '导出码率档',
  `导出url` varchar(512) NULL DEFAULT NULL COMMENT '导出的 MP4 路径',
  `AIGC显式标识` varchar(200) NOT NULL DEFAULT '本内容由人工智能生成' COMMENT '【C7】画面角标/片头文案（《人工智能生成合成内容标识办法》2026-09 施行）',
  `AIGC隐式标识` varchar(512) NULL DEFAULT NULL COMMENT '【C7】写入文件元数据的隐式标识串',
  `合成task_id` bigint(20) NULL DEFAULT NULL COMMENT '合成任务（task.id，ffmpeg 队列）',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_成片_剧集版本`(`剧id` ASC, `集号` ASC, `版本` ASC) USING BTREE,
  CONSTRAINT `fk_成片_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '每集成片；导出强制打 AIGC 标识（C7）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 19. 积分流水 —— 积分两阶段账本（C8：预扣→落账/回退，可对账）
-- ----------------------------
DROP TABLE IF EXISTS `积分流水`;
CREATE TABLE `积分流水`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '流水主键',
  `用户id` bigint(20) NOT NULL COMMENT '所属用户',
  `task_id` bigint(20) NOT NULL COMMENT '关联任务（task.id）；与 task.积分 对账',
  `动作` varchar(10) NOT NULL COMMENT '预扣（任务提交）/ 落账（任务成功）/ 回退（失败/超时/取消）',
  `积分` decimal(10, 2) NOT NULL COMMENT '本笔积分数（正数）；同 task 的 预扣与(落账或回退) 必须等额对冲',
  `说明` varchar(200) NULL DEFAULT NULL COMMENT '业务说明，如 拆分分镜·第1集',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '流水时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_积分流水_用户id`(`用户id` ASC, `创建时间` ASC) USING BTREE,
  INDEX `idx_积分流水_task`(`task_id` ASC) USING BTREE,
  CONSTRAINT `fk_积分流水_用户id` FOREIGN KEY (`用户id`) REFERENCES `用户` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_积分流水_task` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '积分两阶段流水账本（C8）：预扣/落账/回退三动作，可对账' ROW_FORMAT = Dynamic;

-- =====================================================================================
-- 第三部分 数据修改（DML）
-- =====================================================================================

-- 【M1·P0 立即】技能分类预置两个业务内置分类（必须先于前端 4 处接线执行）
INSERT INTO `技能分类` (`名称`, `编码`, `排序`, `系统内置`) VALUES
('剧本创作', 'script_writing', 10, 1),
('视频生成', 'video_gen', 11, 1);

-- 【M4·阶段二】提示词模板补业务页默认引导词（示例骨架，正文按手册第三部分各页"技能"小节填写）
-- INSERT INTO `提示词模板` (`类型`, `系统提示词`, `生成提示词`) VALUES
-- ('生成:/video/shot',   '你是短剧分镜师…',  '逐镜一行：镜号｜场次｜景别｜运镜｜画面｜台词｜时长；台词用剧本原句；每场 2~4 镜…'),
-- ('生成:/video/assets', '你是短剧资产统筹…','逐项：资产ID｜类型｜名称｜别名｜本集关系｜级别｜摘要；人物摘要写满外观细节…'),
-- ('生成:/video/director','你是单镜导演…',   '只重写当前一镜，保持镜号/场次/前后衔接，负面提示保留禁止句式…');

-- 【M7·2026-10-29】题材标签种子：16 个内置标签（/script/new chips 初始数据，可由用户手动添加扩充）
INSERT INTO `题材标签` (`名称`, `系统内置`, `排序`, `用户id`) VALUES
('都市', 1, 0, NULL), ('校园', 1, 1, NULL), ('玄幻', 1, 2, NULL), ('职场', 1, 3, NULL),
('年代', 1, 4, NULL), ('科幻', 1, 5, NULL), ('悬疑', 1, 6, NULL), ('古装', 1, 7, NULL),
('家庭伦理', 1, 8, NULL), ('甜宠', 1, 9, NULL), ('武侠', 1, 10, NULL), ('喜剧', 1, 11, NULL),
('军事', 1, 12, NULL), ('医疗', 1, 13, NULL), ('宫斗', 1, 14, NULL), ('青春', 1, 15, NULL);

-- ----------------------------
-- 24. 人物关系 —— 关系网边表（/script/character 关系网视图，2026-11-02）
-- ----------------------------
DROP TABLE IF EXISTS `人物关系`;
CREATE TABLE `人物关系`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint NOT NULL COMMENT '所属剧',
  `边序` int NULL DEFAULT 0 COMMENT '展示顺序',
  `甲` varchar(50) NOT NULL COMMENT '角色A名',
  `乙` varchar(50) NOT NULL COMMENT '角色B名',
  `类型` varchar(20) NULL COMMENT '羁绊/协作/认可/对立/利用/亲情',
  `关键词` varchar(255) NULL COMMENT '关键词，顿号分隔',
  `说明` text NULL COMMENT '关系说明（可分段：第1-5集 协作（…）；第6集起 羁绊（…））',
  `创建时间` datetime(6) NULL COMMENT '创建时间',
  `更新时间` datetime(6) NULL COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_人物关系_剧id`(`剧id` ASC) USING BTREE,
  CONSTRAINT `fk_人物关系_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '人物关系网边表（/script/character 关系网视图）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 12. 场次（docs 02 第 12 节，7.5 实体化落地，2026-11-02）
-- ----------------------------
DROP TABLE IF EXISTS `场次`;
CREATE TABLE `场次`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `剧本行id` bigint(20) NOT NULL COMMENT '所属剧本行（某剧某集创作版）',
  `场号` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '场次编号，如 1-1',
  `地点` varchar(100) NULL DEFAULT NULL COMMENT '内/外 · 地点 · 时间',
  `人物` varchar(200) NULL DEFAULT NULL COMMENT '出场人物，顿号分隔',
  `道具` varchar(200) NULL DEFAULT NULL COMMENT '出场道具，顿号分隔',
  `正文` text NULL COMMENT '本场正文，一行一个动作/台词，换行分隔',
  `排序` int(11) NOT NULL DEFAULT 0 COMMENT '场次顺序，数字越小越靠前',
  `创建时间` datetime(6) NULL DEFAULT NULL,
  `更新时间` datetime(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_场次_剧本行id`(`剧本行id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '每集剧本下的场次与正文（7.5 实体化落地）' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- 2026-11-03 分镜视频生成线（用户拍板方案）：
--   分镜 表 ALTER：ADD 生成方式 varchar(50) / 生成提示词 text（已执行）
--   新表 分镜视频：一镜多版历史，选中=1 的版进成片（挂业务键 剧id+集号+镜号，分镜全量替换会换行id）
--   新表 分镜图：每镜独立创作资源区（上传/生成；资产图只引用不落这里）
-- ----------------------------

-- ALTER TABLE `分镜`
--   ADD COLUMN `生成方式` varchar(50) NULL DEFAULT NULL COMMENT '本镜选用的生成方式' AFTER `视频状态`,
--   ADD COLUMN `生成提示词` text NULL COMMENT '本镜出视频的正向提示词' AFTER `生成方式`;

CREATE TABLE `分镜视频`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `集号` int(11) NOT NULL COMMENT '集号',
  `镜号` varchar(20) NOT NULL COMMENT '镜号（分镜全量替换会换行id，挂业务键）',
  `方式` varchar(50) NULL DEFAULT NULL COMMENT '生成方式：导演台全能·i2v/参考生视频/多参考生视频/二采重绘',
  `提示词` text NULL COMMENT '本次生成的正向提示词',
  `任务id` bigint(20) NULL DEFAULT NULL COMMENT '来源任务 id（任务表）',
  `url` varchar(512) NULL DEFAULT NULL COMMENT '视频相对路径',
  `状态` varchar(16) NOT NULL DEFAULT '已生成' COMMENT '已生成/失败',
  `选中` tinyint(1) NOT NULL DEFAULT 0 COMMENT '1=该镜当前选用这版（成片取这版）',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_分镜视频_镜`(`剧id` ASC, `集号` ASC, `镜号` ASC) USING BTREE,
  CONSTRAINT `fk_分镜视频_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '分镜视频版本：一镜多版，选中版进成片' ROW_FORMAT = Dynamic;

CREATE TABLE `分镜图`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '行主键',
  `剧id` bigint(20) NOT NULL COMMENT '所属剧',
  `集号` int(11) NOT NULL COMMENT '集号',
  `镜号` varchar(20) NOT NULL COMMENT '镜号',
  `url` varchar(512) NOT NULL COMMENT '图片相对路径，如 上传/xxx.png',
  `标注` varchar(200) NULL DEFAULT NULL COMMENT '标注，如 首帧/李宝明参考',
  `来源` varchar(10) NOT NULL DEFAULT '上传' COMMENT '上传/资产/生成',
  `提示词` text NULL COMMENT '本图生成提示词（来源=生成时）',
  `排序` int(11) NOT NULL DEFAULT 0 COMMENT '显示顺序',
  `创建时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
  `更新时间` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_分镜图_镜`(`剧id` ASC, `集号` ASC, `镜号` ASC) USING BTREE,
  CONSTRAINT `fk_分镜图_剧id` FOREIGN KEY (`剧id`) REFERENCES `剧` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '分镜专属参考图：每镜独立创作资源区' ROW_FORMAT = Dynamic;
