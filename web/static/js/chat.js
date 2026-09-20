document.addEventListener('DOMContentLoaded', function() {
    let sessionId = null;

    setupMarked({ breaks: true });

    initPage();
    showModeBanner();

    // 明确告诉访客回复来自真实模型还是内置演示逻辑，避免误解
    async function showModeBanner() {
        try {
            const res = await fetch('/api/status');
            if (!res.ok) return;
            const data = await res.json();
            const banner = document.getElementById('mode-banner');
            if (banner && data.mode === 'demo') {
                banner.textContent = t('demo_banner');
                banner.style.display = 'block';
            }
        } catch (err) {
            console.error('mode banner failed:', err);
        }
    }

    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('back-btn').addEventListener('click', () => {
        window.location.href = "/problems";
    });
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    async function initPage() {
        try {
            const questionResp = await fetch(`/api/questions/${questionId}`);
            if (!questionResp.ok) throw new Error('question fetch failed');
            const questionData = await questionResp.json();
            displayQuestionDetail(questionData);

            loadKnowledgePoints();
            loadSimilarQuestions();

            const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'en';
            const sessionResp = await fetch('/api/sessions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question_id: questionId, language: lang})
            });
            if (!sessionResp.ok) throw new Error('session create failed');

            const sessionData = await sessionResp.json();
            sessionId = sessionData.session_id;

            addSystemMessage(t('welcome'));

        } catch (error) {
            console.error('initPage failed:', error);
            addSystemMessage(t('err_init'));
        }
    }

    async function loadKnowledgePoints() {
        try {
            const response = await fetch(`/api/questions/${questionId}/knowledge-points`);
            if (!response.ok) throw new Error();
            const data = await response.json();
            displayKnowledgePoints(data);
        } catch (error) {
            console.error('loadKnowledgePoints failed:', error);
        }
    }

    async function loadSimilarQuestions() {
        try {
            const response = await fetch(`/api/questions/${questionId}/similar`);
            if (!response.ok) throw new Error();
            const data = await response.json();
            displaySimilarQuestions(data);
        } catch (error) {
            console.error('loadSimilarQuestions failed:', error);
        }
    }

    async function sendMessage() {
        const userInput = document.getElementById('user-input');
        const message = userInput.value.trim();
        if (!message || !sessionId) return;

        addUserMessage(message);
        userInput.value = '';

        const sendBtn = document.getElementById('send-btn');
        sendBtn.disabled = true;

        const thinkingEl = addThinkingIndicator();

        try {
            const url = `/api/sessions/${sessionId}/messages`;
            const eventSource = new EventSource(`${url}?content=${encodeURIComponent(message)}&_t=${Date.now()}`);

            let firstToken = true;
            let studentContent = '';
            let teacherContent = '';

            eventSource.onmessage = function(event) {
                if (firstToken) {
                    firstToken = false;
                    removeThinkingIndicator(thinkingEl);
                }
                try {
                    const data = JSON.parse(event.data);
                    const content = data.content;
                    const node = data.node;

                    if (node === 'student_agent') {
                        studentContent += content;
                        updateOrCreateMessage('student', studentContent);
                    } else if (node === 'teacher_agent') {
                        teacherContent += content;
                        updateOrCreateMessage('teacher', teacherContent);
                    } else if (node === 'system') {
                        addSystemMessage(content);
                    }
                } catch (err) {
                    console.error('SSE parse error:', err, event.data);
                }
            };

            eventSource.addEventListener('end', function() {
                eventSource.close();
                removeThinkingIndicator(thinkingEl);
                sendBtn.disabled = false;
            });

            eventSource.onerror = function(error) {
                console.error('SSE error:', error);
                eventSource.close();
                removeThinkingIndicator(thinkingEl);
                sendBtn.disabled = false;
                addSystemMessage(t('err_recv'));
            };

        } catch (error) {
            console.error('sendMessage failed:', error);
            removeThinkingIndicator(thinkingEl);
            document.getElementById('send-btn').disabled = false;
            addSystemMessage(t('err_send'));
        }
    }

    function addThinkingIndicator() {
        const container = document.getElementById('chat-messages');
        const el = document.createElement('div');
        el.className = 'message-item thinking-item';
        el.innerHTML = `
            <div class="message-container">
                <div class="message-content">
                    <div class="avatar" style="background:#e0f2fe">
                        <svg class="avatar-icon" style="color:#0284c7" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 10v6M2 10l10-5 10 5-10 5z"></path>
                            <path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"></path>
                        </svg>
                    </div>
                    <div>
                        <div class="thinking-indicator">
                            <div class="dots">
                                <div class="dot"></div>
                                <div class="dot"></div>
                                <div class="dot"></div>
                            </div>
                            <span class="thinking-label" data-i18n="thinking">${t('thinking')}</span>
                        </div>
                        <div class="thinking-bar"></div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(el);
        scrollToBottom();
        return el;
    }

    function removeThinkingIndicator(el) {
        if (el && el.parentNode) el.parentNode.removeChild(el);
    }

    function updateOrCreateMessage(type, content) {
        const container = document.getElementById('chat-messages');
        let messageElement = null;

        if (type === 'student') {
            messageElement = container.querySelector('.message-item:last-child .student-avatar');
            if (!messageElement) {
                const div = document.createElement('div');
                div.className = 'message-item';
                div.innerHTML = `
                    <div class="message-container">
                        <div class="message-content">
                            <div class="avatar student-avatar">
                                <svg class="avatar-icon student-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M22 10v6M2 10l10-5 10 5-10 5z"></path>
                                    <path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"></path>
                                </svg>
                            </div>
                            <div class="message-bubble-container">
                                <div class="message-header">
                                    <span class="sender-name student-name">${t('sender_student')}</span>
                                </div>
                                <div class="message-bubble student-bubble">
                                    <div class="message-text"></div>
                                    <button class="expand-button">
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16">
                                            <polyline points="6 9 12 15 18 9"></polyline>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="connector-line"></div>
                `;
                container.appendChild(div);
                messageElement = container.querySelector('.message-item:last-child');
            } else {
                messageElement = messageElement.closest('.message-item');
            }
        } else if (type === 'teacher') {
            messageElement = container.querySelector('.message-item:last-child .teacher-avatar');
            if (!messageElement) {
                const div = document.createElement('div');
                div.className = 'message-item';
                div.innerHTML = `
                    <div class="message-container">
                        <div class="message-content">
                            <div class="avatar teacher-avatar">
                                <svg class="avatar-icon teacher-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M22 10v6M2 10l10-5 10 5-10 5z"></path>
                                    <path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"></path>
                                </svg>
                            </div>
                            <div class="message-bubble-container">
                                <div class="message-header">
                                    <span class="teacher-badge">${t('badge_teacher')}</span>
                                    <span class="sender-name teacher-name">${t('sender_teacher')}</span>
                                </div>
                                <div class="message-bubble teacher-bubble">
                                    <div class="message-text expanded"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="connector-line"></div>
                `;
                container.appendChild(div);
                messageElement = container.querySelector('.message-item:last-child');
            } else {
                messageElement = messageElement.closest('.message-item');
            }
        }

        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-text');
            if (type === 'teacher') {
                let cleanContent = content
                    .replace(/\n\s*\n\s*\n\s*\n/g, '\n\n')
                    .replace(/\n\s+/g, '\n')
                    .trim();

                const md2html = (text) => {
                    text = text.replace(/^# (.*?)$/gm, '<h3 class="compact-h3">$1</h3>');
                    text = text.replace(/^## (.*?)$/gm, '<h4 class="compact-h4">$1</h4>');
                    text = text.replace(/^### (.*?)$/gm, '<h5 class="compact-h5">$1</h5>');
                    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
                    text = text.replace(/^\s*-\s+(.*?)$/gm, '<li class="compact-li">$1</li>');
                    text = text.replace(/^\s*\*\s+(.*?)$/gm, '<li class="compact-li">$1</li>');
                    text = text.replace(/^\s*(\d+)\.\s+(.*?)$/gm, '<li class="compact-li compact-ol">$1. $2</li>');

                    let inList = false;
                    const lines = text.split('\n');
                    let result = '';
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i];
                        if (line.includes('<li class="compact-li">') || line.includes('<li class="compact-li compact-ol">')) {
                            if (!inList) { result += '<ul class="compact-ul">'; inList = true; }
                            result += line;
                        } else {
                            if (inList) { result += '</ul>'; inList = false; }
                            if (line.trim() !== '' && !line.startsWith('<h') && !line.startsWith('<ul') && !line.startsWith('</ul')) {
                                result += `<p class="compact-p">${line}</p>`;
                            } else {
                                result += line;
                            }
                        }
                    }
                    if (inList) result += '</ul>';
                    return result;
                };

                let html = '';
                cleanContent.split('\n\n').forEach(para => {
                    if (para.trim()) html += md2html(para);
                });
                contentDiv.innerHTML = html;
                contentDiv.classList.add('expanded');
                typesetMath([contentDiv]);
            } else {
                contentDiv.innerHTML = mdToHtml(content);
                const expandButton = messageElement.querySelector('.expand-button');
                setTimeout(() => {
                    const contentHeight = contentDiv.scrollHeight;
                    const lineHeight = parseInt(window.getComputedStyle(contentDiv).lineHeight);
                    if (contentHeight > lineHeight * 3) {
                        expandButton.style.display = 'inline-block';
                        contentDiv.classList.remove('expanded');
                    } else {
                        expandButton.style.display = 'none';
                    }
                    scrollToBottom();
                }, 100);
            }
            scrollToBottom();
        }
    }

    function addUserMessage(message) {
        const container = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-item';
        const isShort = message.length < 15;
        messageDiv.innerHTML = `
            <div class="message-container user">
                <div class="message-content">
                    <div class="avatar user-avatar">
                        <svg class="avatar-icon user-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                    </div>
                    <div class="message-bubble-container">
                        <div class="message-header">
                            <span class="sender-name user-name">${t('sender_you')}</span>
                        </div>
                        <div class="message-bubble user-bubble${isShort ? ' short-message' : ''}">
                            <div class="message-text ${isShort ? 'short-text' : ''}"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="connector-line"></div>
        `;
        const temp = document.createElement('div');
        temp.textContent = message;
        messageDiv.querySelector('.message-text').innerHTML = mdToHtml(temp.textContent);
        container.appendChild(messageDiv);
        scrollToBottom();
    }

    function addSystemMessage(message) {
        const container = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-item';
        messageDiv.innerHTML = `
            <div class="message-container">
                <div class="message-content">
                    <div class="avatar">
                        <svg class="avatar-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                    </div>
                    <div class="message-bubble-container">
                        <div class="message-header">
                            <span class="sender-name">${t('sender_system')}</span>
                        </div>
                        <div class="message-bubble">
                            <div class="message-text"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="connector-line"></div>
        `;
        messageDiv.querySelector('.message-text').textContent = message;
        container.appendChild(messageDiv);
        scrollToBottom();
    }

    function displayQuestionDetail(questionData) {
        const detailDiv = document.getElementById('question-detail');

        const renderMarkdown = (text) => {
            let processedText = text
                .replace(/\n\t\t/g, '\n<span class="double-indent"></span>')
                .replace(/\n\t/g, '\n<span class="indent"></span>')
                .replace(/\n\n\n/g, '\n<br><br>\n')
                .replace(/\n\n/g, '\n<br>\n');
            return mdToHtml(processedText);
        };

        let stem = questionData.content || '';
        let options = [];

        if (questionData.options && Object.keys(questionData.options).length) {
            options = Object.keys(questionData.options).map(k => ({ key: k, text: questionData.options[k] }));
        } else {
            const lines = stem.split('\n');
            const optionRegex = /^\s*([A-Z])[.、)]\s*(.+)$/;
            const stemLines = [];
            let started = false;
            lines.forEach(line => {
                const m = line.match(optionRegex);
                if (m) {
                    started = true;
                    options.push({ key: m[1], text: m[2].trim() });
                } else if (!started) {
                    stemLines.push(line);
                } else if (line.trim() && options.length) {
                    options[options.length - 1].text += ' ' + line.trim();
                }
            });
            if (options.length) stem = stemLines.join('\n');
        }

        const displayTitle = cleanTitle(questionData.title);
        let html = `<div class="question-title">${displayTitle}</div>`;
        html += `<div class="question-content">${renderMarkdown(stem)}</div>`;

        if (options.length) {
            html += '<div class="mcq-options">';
            options.forEach(opt => {
                html += `<button type="button" class="mcq-option" data-key="${opt.key}">`
                      + `<span class="mcq-key">${opt.key}</span>`
                      + `<span class="mcq-text">${opt.text}</span></button>`;
            });
            html += '</div>';
        }

        detailDiv.innerHTML = html;

        detailDiv.querySelectorAll('.mcq-option').forEach(btn => {
            btn.addEventListener('click', () => {
                detailDiv.querySelectorAll('.mcq-option').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                const input = document.getElementById('user-input');
                if (input) {
                    input.value = t('mcq_prefix', { key: btn.dataset.key });
                    input.focus();
                }
            });
        });

        typesetMath([detailDiv]);
        const codeBlocks = detailDiv.querySelectorAll('pre code');
        if (window.hljs && codeBlocks.length > 0) {
            try { codeBlocks.forEach(block => hljs.highlightElement(block)); } catch (e) {}
        }
    }

    function displayKnowledgePoints(kpData) {
        const kpList = document.getElementById('knowledge-points-list');
        kpList.innerHTML = '';
        if (!kpData || kpData.length === 0) {
            kpList.innerHTML = `<li>${t('no_kp')}</li>`;
            return;
        }
        kpData.forEach(kp => {
            const li = document.createElement('li');
            li.className = 'knowledge-point-item';
            li.dataset.id = kp.id;

            const titleSpan = document.createElement('span');
            titleSpan.className = 'knowledge-point-title';
            titleSpan.textContent = kp.title;

            const noteIcon = document.createElement('span');
            noteIcon.className = 'note-icon';
            noteIcon.innerHTML = '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M1 2.828c.885-.37 2.154-.769 3.388-.893 1.33-.134 2.458.063 3.112.752v9.746c-.935-.53-2.12-.603-3.213-.493-1.18.12-2.37.461-3.287.811V2.828zm7.5-.141c.654-.689 1.782-.886 3.112-.752 1.234.124 2.503.523 3.388.893v9.923c-.918-.35-2.107-.692-3.287-.81-1.094-.111-2.278-.039-3.213.492V2.687zM8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783z"/></svg>';

            li.appendChild(titleSpan);
            li.appendChild(noteIcon);

            const popup = document.createElement('div');
            popup.className = 'knowledge-popup';
            popup.textContent = t('kp_loading');
            popup.style.display = 'none';
            li.appendChild(popup);

            li.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (popup.style.display === 'block') { popup.style.display = 'none'; return; }
                popup.style.display = 'block';
                adjustPopupPosition(li, popup);
                if (popup.textContent === t('kp_loading') || popup.textContent === t('kp_loading', {}, 'zh')) {
                    try {
                        const response = await fetch(`/api/knowledge/${kp.id}`);
                        if (response.ok) {
                            popup.innerHTML = mdToHtml(await response.json());
                        } else {
                            popup.textContent = t('kp_fail');
                        }
                    } catch (error) {
                        popup.textContent = t('kp_fail');
                    }
                }
            });

            document.addEventListener('click', function(e) {
                if (!li.contains(e.target)) popup.style.display = 'none';
            });

            kpList.appendChild(li);
        });
    }

    function displaySimilarQuestions(questions) {
        const qList = document.getElementById('similar-questions-list');
        qList.innerHTML = '';
        if (!questions || questions.length === 0) {
            qList.innerHTML = `<li>${t('no_similar')}</li>`;
            return;
        }
        questions.forEach(q => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = `/chat/${q.id}`;
            a.textContent = q.title;
            li.appendChild(a);
            qList.appendChild(li);
        });
    }

    function adjustPopupPosition(element, popup) {
        const rect = element.getBoundingClientRect();
        const popupWidth = popup.offsetWidth;
        if (rect.left + popupWidth > window.innerWidth - 20) {
            popup.style.left = 'auto';
            popup.style.right = '0';
        } else {
            popup.style.left = '0';
            popup.style.right = 'auto';
        }
    }

    function scrollToBottom() {
        const notebookContent = document.querySelector('.notebook-content');
        if (notebookContent) notebookContent.scrollTop = notebookContent.scrollHeight;
    }

    document.addEventListener('click', function(e) {
        if (e.target.closest('.expand-button')) {
            const button = e.target.closest('.expand-button');
            if (button.closest('.teacher-bubble')) return;
            const messageText = button.parentElement.querySelector('.message-text');
            messageText.classList.toggle('expanded');
            button.innerHTML = messageText.classList.contains('expanded')
                ? `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><polyline points="18 15 12 9 6 15"></polyline></svg>`
                : `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><polyline points="6 9 12 15 18 9"></polyline></svg>`;
            setTimeout(scrollToBottom, 100);
        }
    });
});
