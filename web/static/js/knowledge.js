document.addEventListener('DOMContentLoaded', function() {
    // 存储章节数据和知识点数据
    let chapters = [];
    let currentChapter = null;
    let knowledgePoints = {};
    let currentKnowledgeId = null;
    
    // 存储知识点详情信息（id和title）
    let knowledgeDetails = {};
    
    // 获取DOM元素
    const chapterList = document.getElementById('chapter-list');
    const knowledgeList = document.getElementById('knowledge-list');
    const knowledgeDetail = document.getElementById('knowledge-detail');
    const knowledgeTitle = document.getElementById('knowledge-title');
    const knowledgeSummary = document.getElementById('knowledge-summary');
    const currentChapterTitle = document.getElementById('current-chapter-title');
    const emptyDetailPlaceholder = document.getElementById('empty-detail-placeholder');
    
    // 配置marked选项
    setupMarked({
        breaks: true,  // 允许在换行时添加<br>标签
        gfm: true      // 使用GitHub风格的Markdown
    });
    
    // 初始化
    init();
    
    async function init() {
        try {
            // 加载章节数据
            await loadChapters();
            
            // 加载所有知识点的标题
            await loadAllKnowledgeDetails();
        } catch (error) {
            console.error('初始化失败:', error);
            knowledgeList.innerHTML = `<p class="empty-tip">${t('load_fail')}</p>`;
        }
    }
    
    // 加载所有知识点详情信息（标题）
    async function loadAllKnowledgeDetails() {
        try {
            const response = await fetch('/api/knowledge/details/all');
            if (!response.ok) throw new Error('knowledge details request failed');
            knowledgeDetails = await response.json();
        } catch (error) {
            // 不再编造知识点标题：接口失败时留空，由页面显示空状态
            console.error('loadAllKnowledgeDetails failed:', error);
            knowledgeDetails = {};
        }
    }

    // 加载章节列表
    async function loadChapters() {
        try {
            const response = await fetch('/api/chapters');
            if (!response.ok) {
                throw new Error('获取章节数据失败');
            }
            
            chapters = await response.json();
            renderChapters();
            
            // 加载所有章节的知识点
            await loadAllKnowledgePoints();
        } catch (error) {
            console.error('加载章节失败:', error);
            chapterList.innerHTML = `<li class="empty-tip">${t('load_fail')}</li>`;
        }
    }
    
    // 加载所有章节的知识点
    async function loadAllKnowledgePoints() {
        try {
            const response = await fetch('/api/knowledge/chapters');
            if (!response.ok) {
                throw new Error('获取知识点数据失败');
            }
            
            knowledgePoints = await response.json();
        } catch (error) {
            console.error('加载知识点失败:', error);
        }
    }
    
    // 获取知识点标题
    async function getKnowledgeTitle(knowledgeId) {
        // 如果已经有缓存的标题，直接返回
        if (knowledgeDetails[knowledgeId] && knowledgeDetails[knowledgeId].title) {
            return knowledgeDetails[knowledgeId].title;
        }
        
        // 否则从API获取
        try {
            const response = await fetch(`/api/knowledge/${knowledgeId}/title`);
            if (!response.ok) {
                throw new Error('获取知识点标题失败');
            }
            
            const data = await response.json();
            
            // 缓存结果
            if (!knowledgeDetails[knowledgeId]) {
                knowledgeDetails[knowledgeId] = {
                    id: knowledgeId,
                    title: data.title
                };
            } else {
                knowledgeDetails[knowledgeId].title = data.title;
            }
            
            return data.title;
        } catch (error) {
            console.error(`获取知识点 ${knowledgeId} 标题失败:`, error);
            return ""; // 失败时返回空标题
        }
    }
    
    // 渲染章节列表
    function renderChapters() {
        chapterList.innerHTML = '';
        
        chapters.forEach((chapter, idx) => {
            const li = document.createElement('li');
            li.className = 'chapter-item';
            li.dataset.id = chapter.id;
            
            // 添加章节标题和折叠图标
            const titleSpan = document.createElement('span');
            titleSpan.className = 'chapter-title';
            titleSpan.textContent = `${idx + 1}. ${chapter.title}`;
            
            const icon = document.createElement('i');
            icon.className = 'fas fa-chevron-right chapter-icon';
            
            li.appendChild(titleSpan);
            li.appendChild(icon);
            
            // 点击章节切换展开/折叠状态
            li.addEventListener('click', (e) => {
                e.preventDefault();
                toggleChapter(chapter, li);
            });
            
            chapterList.appendChild(li);
        });
    }
    
    // 切换章节展开/折叠状态
    function toggleChapter(chapter, chapterElement) {
        const wasActive = chapterElement.classList.contains('active');
        
        // 重置所有章节的状态
        const allChapters = document.querySelectorAll('.chapter-item');
        allChapters.forEach(item => {
            item.classList.remove('active', 'expanded');
        });
        
        // 如果当前章节之前不是活动的，或者是活动的但不是展开的，则展开它
        if (!wasActive) {
            chapterElement.classList.add('active', 'expanded');
            currentChapter = chapter;
            currentChapterTitle.textContent = ` - ${chapter.title}`;
            loadKnowledgePoints(chapter.id);
        } else {
            // 如果之前是活动的，则折叠它（清空知识点列表）
            currentChapter = null;
            currentChapterTitle.textContent = '';
            knowledgeList.innerHTML = `<p class="empty-tip">${t('select_tip')}</p>`;
        }
    }
    
    // 加载某章节的知识点
    function loadKnowledgePoints(chapterId) {
        const chapterKnowledgePoints = knowledgePoints[chapterId] || [];
        
        if (!chapterKnowledgePoints || chapterKnowledgePoints.length === 0) {
            knowledgeList.innerHTML = `<p class="empty-tip">${t('no_kp')}</p>`;
            return;
        }
        
        knowledgeList.innerHTML = '';
        
        chapterKnowledgePoints.forEach(kpId => {
            const div = document.createElement('div');
            div.className = 'knowledge-item';
            div.dataset.id = kpId;
            
            // 获取知识点标题（如果存在），只显示干净标题，不暴露内部ID
            let kpTitle = knowledgeDetails[kpId] ? knowledgeDetails[kpId].title : "";
            
            const titleDiv = document.createElement('div');
            titleDiv.className = 'knowledge-title-text';
            titleDiv.textContent = kpTitle || t('untitled_kp');
            
            div.appendChild(titleDiv);
            
            // 点击知识点显示详情
            div.addEventListener('click', (e) => {
                e.stopPropagation(); // 防止事件冒泡到章节
                selectKnowledgePoint(kpId, div);
            });
            
            knowledgeList.appendChild(div);
        });
    }
    
    // 选择知识点并显示详情
    function selectKnowledgePoint(knowledgeId, element) {
        // 更新UI选中状态
        const allKnowledgeItems = document.querySelectorAll('.knowledge-item');
        allKnowledgeItems.forEach(item => item.classList.remove('active'));
        if (element) element.classList.add('active');
        
        // 更新当前选中的知识点ID
        currentKnowledgeId = knowledgeId;
        
        // 显示知识点详情
        loadKnowledgeDetail(knowledgeId);
    }
    
    // 加载知识点详情
    async function loadKnowledgeDetail(knowledgeId) {
        try {
            // 隐藏占位符，显示详情面板
            emptyDetailPlaceholder.style.display = 'none';
            knowledgeDetail.style.display = 'flex';
            
            // 获取知识点标题
            const kpDetail = knowledgeDetails[knowledgeId] || { id: knowledgeId, title: "" };
            
            // 如果标题为空，尝试从API获取
            if (!kpDetail.title) {
                kpDetail.title = await getKnowledgeTitle(knowledgeId);
            }
            
            // 只显示干净的知识点标题，不暴露内部ID
            knowledgeTitle.innerHTML = `<span class="knowledge-title-label">${kpDetail.title || t('untitled_kp')}</span>`;
            
            knowledgeSummary.innerHTML = `<div style="text-align: center; padding: 20px;">${t('loading')}</div>`;
            
            // 获取知识点详情
            const response = await fetch(`/api/knowledge/${knowledgeId}`);
            if (!response.ok) {
                throw new Error('获取知识点详情失败');
            }
            
            const summary = await response.json();
            
            // 使用marked将Markdown转换为HTML
            const renderedHTML = mdToHtml(summary);
            
            // 更新UI (仅更新内容，标题已在上面更新)
            knowledgeSummary.innerHTML = renderedHTML;
        } catch (error) {
            console.error('加载知识点详情失败:', error);
            knowledgeSummary.innerHTML = `<div class="error-message">${t('kp_fail')}</div>`;
        }
    }
}); 