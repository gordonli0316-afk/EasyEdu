/**
 * Simple bilingual toggle for EasyEdu.
 * Usage: include this file in every page, then call initI18n() after DOM ready.
 */
const I18N = {
  en: {
    nav_home:      "Home",
    nav_practice:  "Practice",
    nav_knowledge: "Knowledge",
    nav_upload:    "Upload",
    nav_flash:     "Flashcards",
    lang_btn:      "中文",
    // chat page
    focus_mode:    "Focus Timer",
    q_detail:      "Question",
    related_kp:    "Related Knowledge",
    similar_q:     "Similar Questions",
    back:          "Back",
    send:          "Send",
    placeholder:   "Enter your solution and reasoning here...",
    welcome:       "Welcome to EasyEdu! Please share your solution and reasoning below.",
    thinking:      "Reviewing your reasoning...",
    // problems page
    select_subject:"Select a subject",
    chapter_list:  "Chapters",
    question_list: "Questions",
    select_tip:    "Select a subject and chapter to view questions",
    // dynamic strings
    loading:       "Loading...",
    load_fail:     "Failed to load. Please refresh.",
    no_questions:  "No questions in this chapter.",
    diff_easy:     "Easy",
    diff_medium:   "Medium",
    diff_hard:     "Hard",
    type_concept:  "Concept",
    type_calc:     "Calculation",
    type_app:      "Application",
    type_mcq:      "MCQ",
    chat_header:   "Feynman Practice",
    sender_you:    "You",
    sender_system: "Guide",
    sender_student:"Peer",
    sender_teacher:"Tutor",
    badge_teacher: "Tutor",
    no_kp:         "No related knowledge points.",
    no_similar:    "No similar questions.",
    kp_loading:    "Loading...",
    kp_fail:       "Could not load knowledge point.",
    mcq_prefix:    "I choose {key}, because",
    pomo_start:    "Start",
    pomo_pause:    "Pause",
    pomo_resume:   "Resume",
    pomo_reset:    "Reset",
    pomo_done:     "Focus session complete! Take a 5-minute break.",
    err_init:      "Failed to load. Please refresh.",
    err_recv:      "Error receiving response. Please retry.",
    err_send:      "Failed to send. Please retry.",
    // index page
    hero_sub:      "IB / AP Tutoring",
    hero_lead:     "You explain the problem. EasyEdu pushes back until the reasoning is airtight.",
    hero_desc:     "Most study tools show you the answer. EasyEdu asks you to produce it: you write the full solution to a real IB or AP question, an AI study partner challenges the weak steps, and a tutor closes the gaps with the textbook reasoning. If you cannot explain it, you have not learned it yet.",
    hero_cta:      "Try a question now",
    hero_cta2:     "Browse all questions",
    hero_hint:     "No account, no setup — pick a question and start typing.",
    hiw_title:     "How it works",
    hiw_s1_num:    "Step 1",
    hiw_s1_title:  "Pick a real exam question",
    hiw_s1_desc:   "Browse by AP and IB course and chapter. Every question is a full item with a worked reference answer and its underlying knowledge points.",
    hiw_s2_num:    "Step 2",
    hiw_s2_title:  "Explain it in your own words",
    hiw_s2_desc:   "Type your solution the way you would teach a classmate — the reasoning, not just the final number. The tutor reads what you actually wrote.",
    hiw_s3_num:    "Step 3",
    hiw_s3_title:  "Get challenged, then corrected",
    hiw_s3_desc:   "Right but shallow, and your study partner asks the follow-up that exposes the gap. Wrong or finished, and the tutor steps in with the underlying principle.",
    courses_title: "Courses in this build",
    courses_note:  "These courses are loaded from the question bank this server is actually serving.",
    footer_note:   "EasyEdu is an open-source project. Question content is based on published AP and IB course material and is used for study purposes.",
    stat_questions:"Questions",
    stat_chapters: "Chapters",
    stat_subjects: "Courses",
    demo_notice:   "Public demo mode: this copy runs without a live AI model, so the study partner and tutor reply using the built-in worked solutions. The full explain-back loop works exactly as it does with a model attached — nothing else changes.",
    live_notice:   "Live mode: an AI model is connected, so the study partner and tutor respond in their own words.",
    demo_banner:   "Demo mode — responses come from the built-in reference answers, not a live AI model.",
    cards_title:   "Knowledge cards",
    cards_subtitle:"Every card is a knowledge point from the question bank. Read the title, say the explanation out loud, then flip to check yourself.",
    cards_all:     "All courses",
    cards_shuffle: "Shuffle",
    cards_flip:    "Click the card to reveal the explanation",
    cards_flip_back:"Click the card to hide the explanation",
    cards_prev:    "Previous",
    cards_next:    "Next",
    cards_empty:   "No knowledge cards available.",
    untitled_kp:   "Knowledge point",
    kp_chapters:   "Chapters",
    kp_list:       "Knowledge points",
    kp_detail:     "Knowledge point detail",
    kp_pick:       "Choose a knowledge point on the left to read its explanation",
    kp_pick_chapter:"Choose a chapter to see its knowledge points",
    no_bank:       "No question bank is loaded on this server yet.",
  },
  zh: {
    nav_home:      "首页",
    nav_practice:  "题目练习",
    nav_knowledge: "知识点速记",
    nav_upload:    "上传题目",
    nav_flash:     "抽认卡",
    lang_btn:      "EN",
    focus_mode:    "专注模式",
    q_detail:      "题目详情",
    related_kp:    "相关知识点",
    similar_q:     "相似问题",
    back:          "返回列表",
    send:          "发送",
    placeholder:   "输入解题思路与推理过程...",
    welcome:       "欢迎来到 EasyEdu！请在下方阐述你的解题步骤与思路。",
    thinking:      "分析思路中...",
    select_subject:"选择科目",
    chapter_list:  "章节列表",
    question_list: "题目列表",
    select_tip:    "请选择科目和章节查看题目",
    loading:       "加载中...",
    load_fail:     "加载失败，请刷新页面重试",
    no_questions:  "该章节暂无题目",
    diff_easy:     "简单",
    diff_medium:   "中等",
    diff_hard:     "困难",
    type_concept:  "概念题",
    type_calc:     "计算题",
    type_app:      "应用题",
    type_mcq:      "选择题",
    chat_header:   "讲题研讨精练",
    sender_you:    "你",
    sender_system: "课堂提示",
    sender_student:"同学提问",
    sender_teacher:"辅导老师",
    badge_teacher: "教师精讲",
    no_kp:         "暂无相关知识点",
    no_similar:    "暂无相似问题",
    kp_loading:    "加载中...",
    kp_fail:       "加载知识点详情失败",
    mcq_prefix:    "我选 {key}，因为",
    pomo_start:    "开始",
    pomo_pause:    "暂停",
    pomo_resume:   "继续",
    pomo_reset:    "重置",
    pomo_done:     "番茄时间到！你完成了一个专属学习时段，休息5分钟吧！",
    err_init:      "加载失败，请刷新页面重试。",
    err_recv:      "接收消息出错，请重试。",
    err_send:      "发送消息失败，请重试。",
    // index page
    hero_sub:      "IB / AP 课程精练",
    hero_lead:     "你来讲解，EasyEdu 一直追问到推理无懈可击。",
    hero_desc:     "大多数学习工具直接把答案给你，EasyEdu 要你把答案讲出来：面对一道真实的 IB / AP 题目写出完整解法，AI 同学会挑战你站不住的步骤，辅导老师再用教材里的原理补齐缺口。讲不清楚，就是还没学会。",
    hero_cta:      "马上试一道题",
    hero_cta2:     "浏览全部题目",
    hero_hint:     "无需注册、无需配置——选一道题就能开始写。",
    hiw_title:     "学习闭环",
    hiw_s1_num:    "第 1 步",
    hiw_s1_title:  "挑一道真题",
    hiw_s2_desc:   "像给同学讲题一样写下完整解法——重点是推理过程，而不只是最后那个数字。老师看的是你真正写出来的东西。",
    hiw_s1_desc:   "按 AP / IB 课程与章节浏览题库。每道题都配有参考答案与对应知识点。",
    hiw_s2_num:    "第 2 步",
    hiw_s2_title:  "用自己的话讲一遍",
    hiw_s3_num:    "第 3 步",
    hiw_s3_title:  "先被追问，再被纠正",
    hiw_s3_desc:   "讲对了但太浅，AI 同学会继续追问，把漏洞逼出来；讲错了或者已经讲完整，辅导老师会带着底层原理收尾。",
    courses_title: "本次部署收录的课程",
    courses_note:  "以下课程来自这台服务器实际加载的题库。",
    footer_note:   "EasyEdu 是开源项目。题目内容基于公开的 AP / IB 课程资料，仅用于学习目的。",
    stat_questions:"道题目",
    stat_chapters: "个章节",
    stat_subjects: "门课程",
    demo_notice:   "公开演示模式：本次部署未接入实时 AI 模型，AI 同学与辅导老师会基于内置的参考答案与讲解来回应。完整的「讲题 — 追问 — 精讲」流程与接入模型时完全一致。",
    live_notice:   "在线模式：已接入 AI 模型，AI 同学与辅导老师会用模型自己的话回应。",
    demo_banner:   "演示模式——回复来自内置参考答案，而非实时 AI 模型。",
    cards_title:   "知识点抽认卡",
    cards_subtitle:"每张卡片都是题库里的一个知识点。先看标题，把解释讲一遍，再翻面检查自己。",
    cards_all:     "全部课程",
    cards_shuffle: "随机打乱",
    cards_flip:    "点击卡片查看解释",
    cards_flip_back:"点击卡片收起解释",
    cards_prev:    "上一张",
    cards_next:    "下一张",
    cards_empty:   "暂无知识点卡片。",
    untitled_kp:   "知识点",
    kp_chapters:   "章节列表",
    kp_list:       "知识点列表",
    kp_detail:     "知识点详情",
    kp_pick:       "请从左侧选择知识点查看详情",
    kp_pick_chapter:"请选择章节查看知识点",
    no_bank:       "这台服务器目前还没有加载题库。",
  }
};

/**
 * Markdown -> HTML, with a plain-text fallback.
 * Every page loads `marked` from a CDN. If that request is blocked (school
 * network, offline review, CDN outage) `marked` is undefined and the page would
 * otherwise throw; this keeps content readable as plain text instead.
 */
function mdToHtml(text) {
  const src = text == null ? "" : String(text);

  // Markdown treats "\(" as an escaped "(", so a Markdown pass would destroy the
  // LaTeX delimiters before MathJax ever sees them. Lift the math out, render the
  // rest as Markdown, then put the math back verbatim.
  const maths = [];
  const stashed = src.replace(/\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$/g, (m) => {
    maths.push(m);
    return "@@EASYEDU_MATH_" + (maths.length - 1) + "@@";
  });

  let html;
  if (window.marked && typeof window.marked.parse === "function") {
    html = window.marked.parse(stashed);
  } else {
    const div = document.createElement("div");
    div.textContent = stashed;
    html = div.innerHTML.replace(/\n/g, "<br>");
  }

  return html.replace(/@@EASYEDU_MATH_(\d+)@@/g, (_, i) => maths[Number(i)]);
}

/** Configure marked once per page, tolerating a blocked CDN. */
function setupMarked(options) {
  if (window.marked && typeof window.marked.use === "function") {
    window.marked.use(options);
  }
}

/**
 * Typeset LaTeX in the given elements, waiting for MathJax to finish loading.
 * MathJax loads async from a CDN, so a page that renders quickly can call this
 * before `typesetPromise` exists, which would leave raw "\( ... \)" on screen.
 * `MathJax.startup.promise` resolves once the engine is ready.
 */
function typesetMath(elements) {
  if (!window.MathJax || typeof window.MathJax.typesetPromise !== "function") return;
  const run = () => window.MathJax.typesetPromise(elements).catch(() => {});
  const ready = window.MathJax.startup && window.MathJax.startup.promise;
  if (ready && typeof ready.then === "function") {
    ready.then(run, run);
  } else {
    run();
  }
}

function getCurrentLang() {
  return localStorage.getItem("easylang") || "en";
}

function setLang(lang) {
  localStorage.setItem("easylang", lang);
  applyI18n(lang);
  // Let pages re-render strings they built in JavaScript
  document.dispatchEvent(new CustomEvent("easylangchange", { detail: { lang } }));
}

function toggleLang() {
  const next = getCurrentLang() === "en" ? "zh" : "en";
  setLang(next);
}

/** Return localized string for key, with optional {key} substitutions */
function t(key, subs) {
  const lang = getCurrentLang();
  const dict = I18N[lang] || I18N.en;
  let str = dict[key] !== undefined ? dict[key] : (I18N.en[key] || key);
  if (subs) {
    Object.keys(subs).forEach(k => { str = str.replace(`{${k}}`, subs[k]); });
  }
  return str;
}

function applyI18n(lang) {
  const dict = I18N[lang] || I18N.en;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key] !== undefined) el.textContent = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key] !== undefined) el.placeholder = dict[key];
  });
  const btn = document.getElementById("lang-toggle-btn");
  if (btn) btn.textContent = dict.lang_btn;
}

function initI18n() {
  applyI18n(getCurrentLang());
}

/**
 * Strip trailing Chinese parenthetical "(中文...)" from a title when in EN mode.
 * e.g. "Exploring Data (探索数据)" → "Exploring Data"  (EN)
 *      "Exploring Data (探索数据)" → "Exploring Data (探索数据)"  (ZH)
 */
function cleanTitle(title) {
  if (!title) return '';
  if (getCurrentLang() === 'en') {
    return title.replace(/\s*\([^)]*[\u4e00-\u9fff\uff00-\uffef][^)]*\)\s*$/, '').trim();
  }
  return title.trim();
}
