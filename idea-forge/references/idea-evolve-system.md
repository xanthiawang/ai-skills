# Idea Evolve System：科研想法进化系统

## 0. 一句话总结

这个 **idea evolve 系统** 的本质不是“AI 帮你想点子”，而是一个把科研 idea 从灵感筛成论文的进化机器。

它真正做的事情是：

> 生成候选 → 拆成论文命题 → 查已有边界 → 用审稿人视角攻击 → 找唯一修复点 → 排名分流 → 写回系统 → 下轮继续进化。

它最强的地方不是“生成”，而是 **判断、淘汰、修复和记忆**。

---

## 1. 这个系统到底是什么？

它可以被定义为：

> 一个以 `sci.ideas.md` 为总入口、以独立 idea note 为基本单位、以 stage / thesis / evidence / risk / next action 为结构的科研 idea 进化系统。

它不是普通笔记，也不是 brainstorm 文档，而是一个 **paper pipeline 的前端决策系统**。

普通科研笔记是：

> 我想到一个方向，先记下来。

这个系统是：

> 这个方向能不能变成 paper？  
> 它的核心 claim 是什么？  
> 它和已有工作差在哪里？  
> 最小可发表证据包是什么？  
> 审稿人会怎么杀它？  
> 哪一个修复动作能让它升级？  
> 它现在应该推进、搁置、试验，还是淘汰？

所以它真正管理的不是“想法”，而是：

> **idea → proposal → pilot → manuscript → publication** 的整个早期漏斗。

---

## 2. 核心架构

这个系统大概由 6 个核心模块组成。

---

### 2.1 Inbox / Index：`sci.ideas.md`

`sci.ideas.md` 是总目录，不是正文库。

它负责收纳和索引所有严肃 idea：

- Active Ideas
- Agent-generated Ideas
- Current Paper-Idea Series
- Historical Ideas
- Rejected / Dormant / Published Ideas

它的功能类似：

> GitHub issue board + Notion database + paper proposal tracker。

所有 idea 都必须进入这个入口，否则很快就会散掉。

---

### 2.2 独立 idea note

每个认真 idea 都要有自己的独立文件，而不是混在一个长文档里。

例如：

```text
CT-VLM-quality-benchmark.md
PIFlow-HU-preservation.md
AI-offloading-RCT-carryover.md
Reddit-counterpublic-uptake.md
```

每个 note 都是一个小型 paper proposal，而不是随手记录。

---

### 2.3 Stage system：生命周期管理

每个 idea 都有明确状态。

| Stage | 含义 |
|---|---|
| inbox | 捕获了，但还没有 triage |
| paper-idea | 有潜在论文价值，已有 thesis 和 novelty boundary |
| pilot | 需要小规模实验 / 文献 / 数据验证 |
| active-paper | 值得正式写成 manuscript |
| dormant | 有意思，但现在不推进 |
| rejected | 明确不值得继续 |
| published | 已转化为 paper / preprint |

这个 stage system 的意义是：

> 每个 idea 都必须被分流。

否则你会陷入一种状态：

> 每个 idea 都看起来不错，但每个 idea 都没有推进到 paper。

---

### 2.4 Required Sections：强制把 idea 压成 paper structure

每个 paper idea 至少要有这些部分：

1. **Paper Thesis**  
   一句精确 claim，不是 topic。

2. **Refined Verdict**  
   当前判断：值得推进吗？能发什么级别？短板是什么？

3. **Contribution Shape**  
   2–5 个具体贡献。

4. **Prior-Work Boundary**  
   和已有工作的边界在哪里？谁已经做过类似事情？

5. **Minimum Publishable Package**  
   最小可发表证据包是什么？

6. **Core Empirical Claim to Seek**  
   最关键的实证命题是什么？

7. **Experiments / Evidence Needed**  
   需要什么数据、实验、benchmark、proof 或 case study？

8. **Rejection Risks**  
   审稿人最可能从哪里攻击？

9. **Next Actions**  
   下一步具体动作，不是“继续调研”。

这个结构非常关键。它把 idea 从“方向”压成“投稿候选物”。

---

## 3. 它真正 work 的机制

这个系统有 8 个核心动作。

---

### 3.1 Capture：先收进系统

所有 idea 先进入 inbox，不急着判断。

这样可以防止两个问题：

- 灵感丢失；
- 灵感太多，全部混在脑子里。

---

### 3.2 Normalize：把 idea 标准化成 paper claim

原始 idea 往往是模糊的，比如：

> 做一个 CT 图像质量评价 benchmark。

系统会把它压成：

> 通用医学 VLM 在低剂量 CT 后处理图像中会系统性高估诊断图像质量，而 lesion-ROI-level evaluation 能揭示全图评分掩盖的临床失败。

这个变化非常重要。

普通 idea 是 topic。成熟 paper idea 是 claim。

---

### 3.3 Retrieve：拉取文献和已有工作

系统不会只听 AI 自己说“这个 idea 很新”。

它会强制检查：

- 相关领域已有工作；
- 最近论文；
- benchmark；
- 已有方法；
- 相似 claim；
- 失败案例。

也就是说，它把 novelty 判断从“感觉”变成“边界判断”。

---

### 3.4 Anchor：用成功 / 失败论文校准

系统里有一个很关键的概念：**anchors**。

Anchor 是真实参照物，例如：

- 顶刊成功论文；
- field-solid paper；
- incremental paper；
- rejected paper；
- failed idea；
- borderline paper；
- 自己过去的投稿经验；
- 真实 reviewer comment。

没有 anchor，AI 很容易觉得每个 idea 都 promising。  
有 anchor 之后，系统会问：

> 这个 idea 像哪篇成功 paper？  
> 又像哪类失败 idea？  
> 它比成功 anchor 强在哪里？  
> 它避免了失败 anchor 的什么问题？

这就是校准机制。

---

### 3.5 Adversarial Kill Pass：模拟审稿人杀 idea

这是系统最重要的部分之一。

它不是让 AI 夸 idea，而是让 AI 主动攻击 idea：

- 不新；
- 不可做；
- 数据不够；
- claim 太大；
- prior work 已经做过；
- 只是旧 paper 的变体；
- 只是换了数据集；
- 只有工程实现，没有科学命题；
- 需要过重实验，短期不可完成；
- 没有最小可发表包。

这一步的目的不是否定你，而是提前替审稿人杀掉弱点。

---

### 3.6 Repair / Mutation：对 idea 做修复和变异

系统不是简单说“好”或“不好”。

它会给每个 near-miss idea 找一个 **one fix**。

例如：

> 这个 idea 当前不是 top-tier，但如果补上真实 benchmark，就能升级。  
> 这个 idea 当前太大，但如果缩成 lesion-level miscalibration claim，就能推进。  
> 这个 idea 当前像旧工作，但如果换成新的证据标准，就有边界。  
> 这个 idea 当前太重，但如果先做 weekend pilot，就能 go/no-go。

这就是 evolve 的关键。

idea 不是一次生成完的，而是在 critique 后被修复、缩小、变形、升级。

---

### 3.7 Rank + Stage：排序和分流

每轮生成的 idea 不会全部进入主系统。

它会分成：

| 类别 | 处理方式 |
|---|---|
| Top 1–5 | 单独建 note，认真跟踪 |
| Rank 6–10 | 打包进 backlog |
| 明显不行 | rejected / dismissed |
| 有趣但暂不做 | dormant |
| 可快速验证 | pilot |
| 已经成型 | active-paper |

这个设计的重点是：**管理注意力**。

科研中最稀缺的不是 idea，而是你的时间和判断力。

---

### 3.8 Write-back：写回系统

这是它和普通聊天最大的区别。

普通 AI 讨论结束后，idea 还是散的。  
这个系统会把判断结果写回：

- `sci.ideas.md`
- 独立 idea note
- backlog
- rejected patterns
- taste memory
- anchors

因此每次讨论都会变成下一轮判断的基础。

没有 write-back，就没有 evolve。  
只有 write-back，系统才会越来越懂你的研究偏好、拒绝模式和论文标准。

---

## 4. 它最强的几个设计

---

### 4.1 不让 AI 围绕自己的旧论文自嗨

图里反复出现：

> NOT from his own papers  
> once your own papers were excluded  
> don’t anchor generated ideas on your own papers again

这个机制非常重要。

很多 AI idea generation 最大的问题是：AI 会围绕你的旧论文不断扩写，生成看似新、其实只是旧工作的变体。

这个系统强制排除“只从自己 paper 生长出来”的 idea，目的是避免：

- self-citation echo chamber；
- 旧方法换名字；
- 旧框架换对象；
- 旧 claim 放大；
- 没有真正 field-level novelty。

它要求一个 idea 在脱离你已有工作之后，仍然能作为独立 paper 成立。

这才是真正的 novelty test。

---

### 4.2 它不追求所有 idea 都通过，而是追求高淘汰率

图里出现：

> zero cleared the top-shot bar  
> three real near-misses  
> solid + fix

这说明系统非常严。

它不是让 AI 每次都生成 10 个“很棒”的 idea。  
它允许结果是：

> 12 个候选，0 个 clean top-shot，3 个 near-miss。

这反而说明系统有效。

因为真实科研就是这样：大部分 idea 都不值得做。真正有价值的是少数幸存者。

---

### 4.3 它用 Pareto 逻辑判断 idea，而不是一个总分

它不是简单打一个 “good / bad score”。

而是把 idea 拆成多个维度：

- novelty；
- feasibility；
- impact；
- evidence accessibility；
- mechanistic sharpness；
- field-level surprise；
- reviewer defensibility。

一个 idea 可能：

- 很新，但不可做；
- 很可做，但不新；
- 很重要，但证据包太大；
- 很稳，但只能发小刊；
- 很 risky，但如果做成就是 top-tier。

所以不能用平均分。要判断它在多个维度上的结构位置。

这就是 Pareto selection。

---

### 4.4 它重视 “minimum publishable package”

这是一个非常实用的科研原则。

任何 idea 都必须回答：

> 最小可发表证据包是什么？

不是“以后可以做很多东西”，而是：

> 最少需要哪些数据、实验、图表、对比、分析，才能构成一篇 paper？

例如 CT VLM benchmark，最小包可能是：

- 3 个部位：head / chest / abdomen；
- 2 类退化：low-dose noise / denoising blur；
- 2–3 个 VLM；
- 2 名放射科医生；
- global score + ROI-level score；
- failure taxonomy；
- agreement / miscalibration analysis。

如果说不出 minimum publishable package，这个 idea 还不能进入 active-paper。

---

### 4.5 它把拒绝理由也当成资产

被 reject 的 idea 不只是删掉，而是记录为什么被杀。

例如：

- 过度 meta-science；
- 太重；
- 已有工作太接近；
- 不想做湿实验；
- 只是自己旧 paper 的变体；
- 数据不可获得；
- 没有明确实证 claim；
- 只是一堆概念组合。

这些 rejected patterns 未来会成为过滤器。

这叫 **negative preference learning**。

系统不是只学习你喜欢什么，也学习你不想再浪费时间做什么。

---

## 5. 深层本质

最深层地看，它不是 idea generator，而是一个：

> **科研判断外显化系统。**

很多成熟研究者脑子里都有类似判断：

- 这个 idea 能不能发？
- 这个 claim 是否太大？
- 数据是否够？
- reviewer 会怎么打？
- 是 main paper 还是 appendix？
- 是现在做还是以后做？
- 是该杀还是该救？

这个系统把这些隐性判断全部结构化、文本化、可追踪化。

所以它真正自动化的不是想象力，而是：

> **科研判断流程。**

科研里最便宜的是 idea。最贵的是判断。

这个系统真正有价值的地方，就是让 AI 不再只是“灵感机器”，而是变成：

- 候选生成器；
- 文献边界检查器；
- 敌意审稿人；
- anchor 校准器；
- proposal 编辑器；
- 项目分流器；
- write-back agent。

---

## 6. 如何借鉴它

你不需要完全复刻它的代码。你最应该借鉴的是它的制度。

可以建立一个自己的 **PaperForge / 论文想法进化器**。

结构可以这样：

```text
/paper_forge
  index.md
  taste.md
  anchors.md
  rejected_patterns.md

  /ideas
    PIFlow-HU-preservation.md
    CT-VLM-quality-benchmark.md
    AI-offloading-RCT-carryover.md
    Reddit-counterpublic-uptake.md

  /anchors
    MedIA-anchor-001.md
    MICCAI-anchor-001.md
    NM&S-anchor-001.md
    NHB-anchor-001.md

  /backlog
    agent-generated-2026-07.md
```

---

## 7. 推荐 idea note 模板

```markdown
# Idea Title

## Stage
inbox / paper-idea / pilot / active-paper / dormant / rejected / submitted / published

## Paper Thesis
一句话说明这篇 paper 要证明什么。必须是 precise claim，不是 topic。

## Refined Verdict
当前判断：是否值得推进？能发什么级别？最大短板是什么？

## Contribution Shape
1.
2.
3.

## Prior-Work Boundary
已有工作做到哪里？我和它们的差别是什么？

## Minimum Publishable Package
这篇文章最小可发表证据包是什么？

## Core Empirical Claim
最关键的实证命题是什么？什么结果能让这篇文章成立？

## Experiments / Evidence Needed
需要什么数据、实验、benchmark、proof 或 case study？

## Best Anchor
它最像哪篇成功 paper？为什么？

## Failure Anchor
它最像哪类失败 idea？需要避免什么？

## Reviewer Kill Pass
审稿人最可能怎么攻击？

## One Fix
只做一件事，什么最能把它提高一个档位？

## Next Action
下一步具体动作，最好是 24–72 小时内能做的。

## Verdict
top-shot / field-solid / solid+fix / near-miss / dormant / rejected
```

---

## 8. 示例 1：CT VLM Quality Benchmark

原始 idea：

> 做 CT 图像质量评价 benchmark，用大模型评价低剂量 CT 去噪效果。

进化后：

```markdown
# CT-VLM Quality Benchmark

## Stage
paper-idea → pilot

## Paper Thesis
General medical VLMs systematically overestimate diagnostic image quality after low-dose CT denoising, and lesion-ROI-level evaluation reveals clinically relevant failures that are hidden by global image-quality scoring.

## Refined Verdict
Promising field-solid benchmark paper. Not yet top-tier unless it demonstrates a clear mismatch between VLM preference and radiologist lesion-level judgment.

## Contribution Shape
1. A CT-specific image-quality rubric separating noise, blur, artifacts, HU stability, and lesion visibility.
2. A paired evaluation of VLM judgments and radiologist ratings under LDCT and post-processed CT.
3. A failure taxonomy showing when VLMs prefer visually smooth but diagnostically degraded images.

## Prior-Work Boundary
Different from general medical VQA benchmarks because the target is not diagnosis QA but image-quality judgment under acquisition and reconstruction degradation.
Different from denoising papers because the benchmark evaluates evaluator reliability, not only denoising performance.

## Minimum Publishable Package
- 3 anatomical regions: head, chest, abdomen
- 2 degradation types: low-dose noise and denoising blur/artifact
- 2–3 VLMs
- 2 radiologists
- Global + ROI-level scoring
- Agreement analysis and failure taxonomy

## Core Empirical Claim
VLM global quality ratings are less sensitive than radiologists to lesion-level degradation caused by denoising or low-dose artifacts.

## Experiments Needed
1. 30–60 representative CT cases.
2. Radiologist Likert scoring.
3. VLM prompting under fixed rubric.
4. Agreement/miscalibration analysis.
5. Qualitative failure examples.

## Rejection Risks
- Dataset too small.
- VLM prompts unstable.
- Radiologist agreement low.
- No real clinical task.
- Contribution looks like engineering dataset, not scientific claim.

## One Fix
Anchor every image-quality judgment to lesion-level visibility and HU/SD stability, not generic visual preference.

## Next Action
Select 10 pilot cases across head/chest/abdomen and test whether VLMs prefer denoised images that radiologists mark as blurred or lesion-degraded.
```

---

## 9. 示例 2：PIFlow Legacy Scanner Generalization

原始 idea：

> PIFlow 可以继续做低剂量 CT 老旧机型泛化。

进化后：

```markdown
# PIFlow Legacy Scanner Generalization

## Stage
active-paper

## Paper Thesis
A zero-shot flow-matching LDCT denoising model trained only on unpaired NDCT images can preserve ROI-level HU means while reducing noise on unseen legacy-scanner clinical LDCT, outperforming self-supervised image-domain baselines without paired data or scanner-specific retraining.

## Refined Verdict
Strong MedIA/MIA-style method paper if the claim stays focused on unpaired training, unseen scanner generalization, and quantitative HU preservation.

## Contribution Shape
1. Flow-matching prior trained on unpaired NDCT.
2. Observation-guided flow interpolation for LDCT-conditioned inference.
3. Patch-integral invariance constraint to reduce HU drift.
4. Legacy-scanner clinical validation with ROI HU stability.

## Minimum Publishable Package
- Public paired piglet benchmark
- Simulated clinical benchmark with paired NDCT
- Legacy clinical unpaired dataset
- Baselines: BM3D, N2S, Noise2Sim, Zero-N2N, SS-N2N, P2P, VQ-SCD
- ROI HU mean/SD analysis
- Ablation: ODE steps, β/η, PIIC on/off

## Core Empirical Claim
PIIC and observation-guided flow interpolation reduce noise while preserving ROI-level HU means better than representative self-supervised and zero-shot baselines.

## Rejection Risks
- Zero-shot claim considered overstated.
- PIIC ablation insufficient.
- Legacy dataset lacks NDCT reference.
- Clinical evaluation only visual/ROI, no reader study.
- Baselines may be challenged.

## One Fix
Make HU preservation the central differentiator and add PIIC on/off ablation on legacy-scanner ROIs.

## Next Action
Finalize PIIC ablation table and ensure all claims avoid implying paired or spatially aligned clinical data are used.
```

---

## 10. 对你的核心启发

你现在不是缺 idea。你真正的问题是：

> idea 很多，但每个 idea 都需要被判断、压缩、分流和推进。

所以你最应该学它的三条原则。

---

### 10.1 每个 idea 必须变成一句 thesis

不要写：

> 做医学影像大模型评价。

要写：

> 通用医学 VLM 在低剂量 CT 后处理图像中会系统性高估病灶可见性，而 ROI-level rubric 能揭示这种误校准。

不要写：

> 做 AI 教育 RCT。

要写：

> 自适应苏格拉底干预可以减少 AI 辅助学习中的 cognitive offloading，并在 support-removed task 中留下 carryover signal。

不要写：

> 做 Reddit counterpublic。

要写：

> 在 ranked local publics 中，issue field 和 post-level counterpublic potential 比 visibility tier 更能预测 counterpublic candidate density。

---

### 10.2 每个 thesis 必须有 minimum publishable package

没有最小证据包，就不是 paper idea。

你每个方向都要问：

> 最少需要什么数据、实验、图、表、对比和分析，才能投稿？

---

### 10.3 每个 package 必须经过 reviewer kill pass

你必须提前问：

> 审稿人会从哪里杀它？

比如：

- 数据太少；
- claim 太大；
- 贡献不清楚；
- 文献边界不够；
- 方法只是组合；
- benchmark 没有临床意义；
- 没有统计检验；
- 没有消融；
- 没有人类标注一致性；
- 没有 reader study；
- 没有 external validation。

能经受住 kill pass 的 idea，才值得进入 active-paper。

---

## 11. 最终公式

这个系统真正厉害的地方是：

> 它把 AI 从“帮我想点子的人”变成了“科研 idea 的变异生成器、敌意审稿人、文献边界检查器、证据包设计器、项目分流器和长期记忆系统”。

它的本质不是提高 idea 数量，而是提高 **idea 的死亡率和幸存者质量**。

最适合你的使用方式是：

> 用它管理你的所有论文方向，把每个方向都压成 thesis、minimum publishable package、rejection risks 和 next action；然后只推进那些通过 kill pass、能做 pilot、并且有明确 one-fix 的 idea。

最终公式：

```text
Raw idea
→ Paper thesis
→ Prior-work boundary
→ Minimum publishable package
→ Reviewer kill pass
→ One-fix repair
→ Stage decision
→ Next action
→ Write-back
→ Evolution
```
