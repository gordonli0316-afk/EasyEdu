function formatDifficulty(d) {
    if (typeof d === 'number') {
        if (d <= 2) return { label: t('diff_easy'), cls: 'easy' };
        if (d >= 4) return { label: t('diff_hard'), cls: 'hard' };
        return { label: t('diff_medium'), cls: 'medium' };
    }
    if (d === '简单' || d === 'easy' || d === 'Easy') return { label: t('diff_easy'), cls: 'easy' };
    if (d === '困难' || d === 'hard' || d === 'Hard') return { label: t('diff_hard'), cls: 'hard' };
    return { label: t('diff_medium'), cls: 'medium' };
}

function formatType(tp) {
    const map = {
        'concept':         'type_concept',
        'calculation':     'type_calc',
        'application':     'type_app',
        'multiple-choice': 'type_mcq',
        'mcq':             'type_mcq',
    };
    return map[tp] ? t(map[tp]) : (tp || t('type_concept'));
}

document.addEventListener('DOMContentLoaded', function() {
    let chapters = [];
    let currentChapter = null;
    let currentSubject = '';

    const subjectSelect = document.getElementById('subject-select');
    const chapterList   = document.getElementById('chapter-list');
    const questionList  = document.getElementById('question-list');
    const currentChapterTitle = document.getElementById('current-chapter-title');

    setupMarked({ breaks: true, gfm: true });

    init();

    async function init() {
        try {
            await loadSubjects();
            await loadChapters();
        } catch (error) {
            console.error('init failed:', error);
            questionList.innerHTML = `<p class="empty-tip">${t('load_fail')}</p>`;
        }
    }

    async function loadSubjects() {
        try {
            const response = await fetch('/api/subjects');
            if (!response.ok) throw new Error('subjects fetch failed');
            const data = await response.json();
            const subjects = Array.isArray(data) ? data : (data.subjects || []);

            subjects.forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.id;
                option.textContent = subject.name;
                subjectSelect.appendChild(option);
            });

            subjectSelect.addEventListener('change', (e) => {
                currentSubject = e.target.value;
                loadChapters();
            });
        } catch (error) {
            console.error('loadSubjects failed:', error);
        }
    }

    async function loadChapters() {
        try {
            chapterList.innerHTML = `<li class="empty-tip">${t('loading')}</li>`;

            let url = '/api/chapters';
            if (currentSubject) url += `?subject=${currentSubject}`;

            const response = await fetch(url);
            if (!response.ok) throw new Error('chapters fetch failed');

            const raw = await response.json();
            // Deduplicate using the CLEANED title so "Foo (中文)" and "Foo (另一个)" collapse into one
            const seen = new Set();
            chapters = raw.filter(ch => {
                const key = cleanTitle(ch.title).toLowerCase();
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });

            renderChapters();
        } catch (error) {
            console.error('loadChapters failed:', error);
            chapterList.innerHTML = `<li class="empty-tip">${t('load_fail')}</li>`;
        }
    }

    function renderChapters() {
        chapterList.innerHTML = '';
        if (chapters.length === 0) {
            chapterList.innerHTML = `<li class="empty-tip">${t('no_bank')}</li>`;
            currentChapterTitle.textContent = '';
            questionList.innerHTML = `<p class="empty-tip">${t('no_bank')}</p>`;
            return;
        }
        chapters.forEach((chapter, idx) => {
            const li = document.createElement('li');
            li.className = 'chapter-item';
            li.dataset.id = chapter.id;
            // Show only the clean English/plain title, strip bilingual suffix like (中文)
            const displayTitle = cleanTitle(chapter.title);
            li.textContent = `${idx + 1}. ${displayTitle}`;
            li.addEventListener('click', () => selectChapter(chapter));
            chapterList.appendChild(li);
        });

        if (chapters.length > 0) selectChapter(chapters[0]);
    }

    function selectChapter(chapter) {
        currentChapter = chapter;
        document.querySelectorAll('.chapter-item').forEach(item => {
            item.classList.toggle('active', item.dataset.id === chapter.id);
        });
        currentChapterTitle.textContent = ` - ${cleanTitle(chapter.title)}`;
        loadQuestions(chapter.id);
    }

    async function loadQuestions(chapterId) {
        try {
            questionList.innerHTML = `<p class="empty-tip">${t('loading')}</p>`;
            const response = await fetch(`/api/chapters/${chapterId}/questions`);
            if (!response.ok) throw new Error('questions fetch failed');
            const questions = await response.json();
            renderQuestions(questions);
        } catch (error) {
            console.error('loadQuestions failed:', error);
            questionList.innerHTML = `<p class="empty-tip">${t('load_fail')}</p>`;
        }
    }

    function renderQuestions(questions) {
        if (!questions || questions.length === 0) {
            questionList.innerHTML = `<p class="empty-tip">${t('no_questions')}</p>`;
            return;
        }
        questionList.innerHTML = '';
        questions.forEach(question => {
            const div = document.createElement('div');
            div.className = 'question-item';
            const { label: diffLabel, cls: diffCls } = formatDifficulty(question.difficulty);
            const typeLabel = formatType(question.type);
            // Clean Chinese suffix from question title in EN mode
            const cleanedTitle = cleanTitle(question.title || '');
            const titleHTML = mdToHtml(cleanedTitle).replace(/<\/?p>/g, '');
            div.innerHTML = `
                <div class="title">${titleHTML}</div>
                <div class="meta">
                    <span>${typeLabel}</span>
                    <span class="difficulty ${diffCls}">${diffLabel}</span>
                </div>
            `;
            div.addEventListener('click', () => { window.location.href = `/chat/${question.id}`; });
            questionList.appendChild(div);
        });
    }
});
