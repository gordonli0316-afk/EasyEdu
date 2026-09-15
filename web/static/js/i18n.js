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
    hero_desc:     "Move beyond passive answer reading. Explain your steps, respond to targeted peer questions, and master each concept with mentor guidance.",
    hero_cta:      "Start practising",
    hiw_title:     "How it works",
    hiw_s1_num:    "Step 1",
    hiw_s1_title:  "Pick a question",
    hiw_s1_desc:   "Browse questions organised by AP and IB course and chapter. Every question comes from the actual textbook.",
    hiw_s2_num:    "Step 2",
    hiw_s2_title:  "Explain your reasoning",
    hiw_s2_desc:   "Type your answer as if teaching a peer. Focus on the core mechanism behind each formula.",
    hiw_s3_num:    "Step 3",
    hiw_s3_title:  "Deepen your understanding",
    hiw_s3_desc:   "Receive targeted follow-ups on surface-level steps, and tailored guidance from the tutor whenever you encounter a conceptual gap.",
    courses_title: "Courses available",
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
    hero_desc:     "告别单纯死记硬背与被动看答案。由你主讲解题逻辑，同伴启发式追问，导师点拨重难点，让知识真正融会贯通。",
    hero_cta:      "开始练习",
    hiw_title:     "学习闭环",
    hiw_s1_num:    "第 1 步",
    hiw_s1_title:  "挑选题目",
    hiw_s1_desc:   "按 AP 与 IB 权威课程与章节精选题库，全面贴合考纲要求。",
    hiw_s2_num:    "第 2 步",
    hiw_s2_title:  "主讲思路",
    hiw_s2_desc:   "自主写出完整解题逻辑与因果推导，而不只是给出孤立公式或选项。",
    hiw_s3_num:    "第 3 步",
    hiw_s3_title:  "追问与精讲",
    hiw_s3_desc:   "当思路尚浅时接收针对性追问；遇到知识断层时，由辅导老师提供梯度点拨与考点归纳。",
    courses_title: "已支持课程",
  }
};

function getCurrentLang() {
  return localStorage.getItem("easylang") || "en";
}

function setLang(lang) {
  localStorage.setItem("easylang", lang);
  applyI18n(lang);
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
