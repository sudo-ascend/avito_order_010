const updateGiftGallery = (gallery, nextIndex) => {
    const track = gallery.querySelector('[data-gift-gallery-track]');
    const slideCount = Number.parseInt(gallery.dataset.galleryLength || '0', 10);

    if (!track || slideCount <= 0) {
        return;
    }

    const normalizedIndex = ((nextIndex % slideCount) + slideCount) % slideCount;

    gallery.dataset.galleryIndex = String(normalizedIndex);
    track.style.transform = `translateX(-${normalizedIndex * 100}%)`;
};

const setupGiftGallery = (gallery) => {
    if (gallery.dataset.galleryReady === 'true') {
        return;
    }

    gallery.dataset.galleryReady = 'true';
    updateGiftGallery(gallery, Number.parseInt(gallery.dataset.galleryIndex || '0', 10));

    const previousButton = gallery.querySelector('[data-gift-gallery-prev]');
    const nextButton = gallery.querySelector('[data-gift-gallery-next]');

    [previousButton, nextButton].forEach((button, index) => {
        if (!button) {
            return;
        }

        button.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();

            const currentIndex = Number.parseInt(gallery.dataset.galleryIndex || '0', 10);
            updateGiftGallery(gallery, currentIndex + (index === 0 ? -1 : 1));
        });
    });
};

const setupGiftGalleries = (root = document) => {
    root.querySelectorAll('[data-gift-gallery]').forEach(setupGiftGallery);
};

setupGiftGalleries();

(() => {
    const menu = document.querySelector('#siteMenu');
    const menuToggle = document.querySelector('.menu-toggle');
    const menuBackdrop = document.querySelector('[data-menu-backdrop]');

    if (!menu || !menuToggle || !menuBackdrop) {
        return;
    }

    const setMenuState = (isOpen) => {
        menu.classList.toggle('show', isOpen);
        document.body.classList.toggle('menu-is-open', isOpen);
        menuBackdrop.classList.toggle('is-visible', isOpen);
        menuBackdrop.tabIndex = isOpen ? 0 : -1;
        menuToggle.setAttribute('aria-expanded', String(isOpen));
    };

    const closeMenu = () => setMenuState(false);

    menuToggle.addEventListener('click', () => setMenuState(!menu.classList.contains('show')));
    menuBackdrop.addEventListener('click', closeMenu);
    menu.querySelectorAll('a[href^="#"]').forEach((link) => {
        link.addEventListener('click', closeMenu);
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && menu.classList.contains('show')) {
            closeMenu();
            menuToggle.focus();
        }
    });
})();

(() => {
    const slider = document.querySelector('[data-product-slider]');

    if (!slider) {
        return;
    }

    const viewport = slider.querySelector('[data-slider-viewport]');
    const track = slider.querySelector('.gift-grid');
    const previousButton = slider.querySelector('[data-slider-prev]');
    const nextButton = slider.querySelector('[data-slider-next]');
    const dots = document.querySelector('[data-slider-dots]');

    if (!viewport || !track || !previousButton || !nextButton || !dots) {
        return;
    }

    const originalCards = [...track.querySelectorAll('.gift-card')];

    if (originalCards.length === 0) {
        return;
    }

    let realPageCount = 0;
    let allPages = [];
    let settleTimer = 0;
    let resizeTimer = 0;

    const cardsPerPage = () => {
        if (window.matchMedia('(max-width: 767.98px)').matches) {
            return 1;
        }

        if (window.matchMedia('(max-width: 991.98px)').matches) {
            return 2;
        }

        if (window.matchMedia('(max-width: 1399.98px)').matches) {
            return 3;
        }

        return 4;
    };

    const chunkCards = (items, size) => {
        const pages = [];

        for (let index = 0; index < items.length; index += size) {
            pages.push(items.slice(index, index + size));
        }

        return pages;
    };

    const buildPage = (cards, columns) => {
        const page = document.createElement('div');

        page.className = 'gift-page';
        page.style.gridTemplateColumns = `repeat(${columns}, minmax(0, 1fr))`;
        page.style.gap = getComputedStyle(track).gap;
        cards.forEach((card) => page.append(card));
        return page;
    };

    const currentInternalPage = () => {
        if (allPages.length === 0) {
            return 0;
        }

        const currentOffset = viewport.scrollLeft;
        let closestIndex = 0;
        let closestDistance = Number.POSITIVE_INFINITY;

        allPages.forEach((page, index) => {
            const distance = Math.abs(page.offsetLeft - currentOffset);

            if (distance < closestDistance) {
                closestDistance = distance;
                closestIndex = index;
            }
        });

        return closestIndex;
    };

    const displayPage = () => {
        const internalPage = currentInternalPage();

        if (realPageCount <= 1) {
            return 0;
        }

        if (internalPage <= 0) {
            return realPageCount - 1;
        }

        if (internalPage >= allPages.length - 1) {
            return 0;
        }

        return internalPage - 1;
    };

    const scrollToInternalPage = (pageIndex, behavior = 'smooth') => {
        const targetPage = allPages[pageIndex];

        if (!targetPage) {
            return;
        }

        if (behavior === 'auto') {
            const previousScrollBehavior = viewport.style.scrollBehavior;

            viewport.style.scrollBehavior = 'auto';
            viewport.scrollLeft = targetPage.offsetLeft;
            window.requestAnimationFrame(() => {
                viewport.style.scrollBehavior = previousScrollBehavior;
            });
            return;
        }

        viewport.scrollTo({
            left: targetPage.offsetLeft,
            behavior,
        });
    };

    const updateControls = () => {
        const page = displayPage();
        const total = Math.max(realPageCount, 1);

        previousButton.disabled = realPageCount <= 1;
        nextButton.disabled = realPageCount <= 1;
        dots.replaceChildren(
            ...Array.from({ length: total }, (_, index) => {
                const dot = document.createElement('span');
                dot.classList.toggle('is-active', index === page);
                return dot;
            }),
        );
    };

    const normalizeLoopPosition = () => {
        if (realPageCount <= 1) {
            updateControls();
            return;
        }

        const internalPage = currentInternalPage();

        if (internalPage <= 0) {
            scrollToInternalPage(realPageCount, 'auto');
        } else if (internalPage >= allPages.length - 1) {
            scrollToInternalPage(1, 'auto');
        }

        updateControls();
    };

    const scheduleLoopSync = () => {
        window.clearTimeout(settleTimer);
        settleTimer = window.setTimeout(normalizeLoopPosition, 140);
        window.requestAnimationFrame(updateControls);
    };

    const renderPages = (preferredPage = 0) => {
        const pageSize = cardsPerPage();
        const pageCards = chunkCards(originalCards, pageSize);
        const pages = pageCards.map((cards) => buildPage(cards, pageSize));

        realPageCount = pages.length;
        track.classList.add('gift-grid--paged');

        if (realPageCount <= 1) {
            track.replaceChildren(...pages);
            allPages = [...track.children];
            viewport.scrollLeft = 0;
            setupGiftGalleries(track);
            updateControls();
            return;
        }

        const leadingClone = pages[pages.length - 1].cloneNode(true);
        const trailingClone = pages[0].cloneNode(true);

        leadingClone.dataset.clone = 'leading';
        trailingClone.dataset.clone = 'trailing';
        leadingClone.setAttribute('aria-hidden', 'true');
        trailingClone.setAttribute('aria-hidden', 'true');

        track.replaceChildren(leadingClone, ...pages, trailingClone);
        allPages = [...track.children];
        setupGiftGalleries(track);

        const nextPage = Math.min(Math.max(preferredPage, 0), realPageCount - 1) + 1;
        viewport.scrollLeft = 0;
        scrollToInternalPage(nextPage, 'auto');
        updateControls();
    };

    const move = (direction) => {
        if (realPageCount <= 1) {
            return;
        }

        const internalPage = currentInternalPage();
        const page = displayPage();

        if (direction > 0 && page >= realPageCount - 1) {
            scrollToInternalPage(internalPage + 1);
            return;
        }

        if (direction < 0 && page <= 0) {
            scrollToInternalPage(internalPage - 1);
            return;
        }

        scrollToInternalPage(internalPage + direction);
    };

    previousButton.addEventListener('click', () => move(-1));
    nextButton.addEventListener('click', () => move(1));
    viewport.addEventListener('scroll', scheduleLoopSync, { passive: true });
    window.addEventListener('resize', () => {
        const activePage = displayPage();

        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(() => renderPages(activePage), 120);
    });

    renderPages();
})();

(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }

    const selectors = [
        ['.about-grid', 0],
        ['.gifts-section .section-heading', 0],
        ['.gift-slider-shell', 80],
        ['.process-section .section-heading', 0],
        ['.process-card', 90],
        ['.works-section .section-heading', 0],
        ['.work-card', 65],
        ['.works-action', 110],
        ['.reviews-section .section-heading', 0],
        ['.reviews-panel', 90],
        ['.contact-panel', 0],
        ['.site-footer .footer-grid', 0],
    ];
    const elements = new Set();

    selectors.forEach(([selector, delayStep]) => {
        document.querySelectorAll(selector).forEach((element, index) => {
            element.classList.add('reveal-on-scroll');
            element.style.setProperty('--reveal-delay', `${Math.min(index * delayStep, 390)}ms`);
            elements.add(element);
        });
    });

    if (!('IntersectionObserver' in window)) {
        elements.forEach((element) => element.classList.add('is-visible'));
        return;
    }

    document.documentElement.classList.add('has-motion');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        rootMargin: '0px 0px -48px',
        threshold: 0.12,
    });

    elements.forEach((element) => observer.observe(element));
})();

(() => {
    const slider = document.querySelector('[data-review-slider]');

    if (!slider) {
        return;
    }

    const viewport = slider.querySelector('[data-review-viewport]');
    const cards = [...slider.querySelectorAll('.review-card')];
    const previousButton = slider.querySelector('[data-review-prev]');
    const nextButton = slider.querySelector('[data-review-next]');
    const dots = slider.querySelector('[data-review-dots]');

    if (!viewport || cards.length === 0 || !previousButton || !nextButton || !dots) {
        return;
    }

    const visibleCardsCount = () => {
        const cardWidth = cards[0].getBoundingClientRect().width;
        return cardWidth ? Math.max(1, Math.round(viewport.clientWidth / cardWidth)) : 1;
    };

    const pageCount = () => Math.ceil(cards.length / visibleCardsCount());

    const currentPage = () => {
        const width = viewport.clientWidth;
        return width ? Math.min(pageCount() - 1, Math.round(viewport.scrollLeft / width)) : 0;
    };

    const updateControls = () => {
        const page = currentPage();
        const total = pageCount();

        previousButton.disabled = page === 0;
        nextButton.disabled = page >= total - 1;
        dots.replaceChildren(
            ...Array.from({ length: total }, (_, index) => {
                const dot = document.createElement('span');
                dot.classList.toggle('is-active', index === page);
                return dot;
            }),
        );
    };

    const move = (direction) => {
        viewport.scrollBy({
            left: direction * viewport.clientWidth,
            behavior: 'smooth',
        });
    };

    previousButton.addEventListener('click', () => move(-1));
    nextButton.addEventListener('click', () => move(1));
    viewport.addEventListener('scroll', () => window.requestAnimationFrame(updateControls), { passive: true });
    window.addEventListener('resize', updateControls);

    updateControls();
})();

(() => {
    const hasLink = (value) => /(https?:\/\/|www\.|t\.me\/)/i.test(value || '');

    const extractPhoneDigits = (value) => {
        let digits = (value || '').replace(/\D/g, '');

        if (digits.startsWith('8')) {
            digits = `7${digits.slice(1)}`;
        } else if (digits && !digits.startsWith('7')) {
            digits = `7${digits}`;
        }

        return digits.slice(0, 11);
    };

    const formatPhoneDigits = (digits) => {
        const area = digits.slice(1, 4);
        const first = digits.slice(4, 7);
        const second = digits.slice(7, 9);
        const third = digits.slice(9, 11);

        let result = '+7';
        if (area) {
            result += ` (${area}`;
            if (area.length === 3) {
                result += ')';
            }
        }
        if (first) {
            result += ` ${first}`;
        }
        if (second) {
            result += `-${second}`;
        }
        if (third) {
            result += `-${third}`;
        }

        return result;
    };

    const normalizePhoneInput = (input) => {
        input.value = formatPhoneDigits(extractPhoneDigits(input.value));
    };

    const setCursorByDigitIndex = (input, digitIndex) => {
        const { value } = input;

        if (digitIndex <= 0) {
            input.setSelectionRange(0, 0);
            return;
        }

        let digitsSeen = 0;
        for (let index = 0; index < value.length; index += 1) {
            if (/\d/.test(value[index])) {
                digitsSeen += 1;
                if (digitsSeen >= digitIndex) {
                    input.setSelectionRange(index + 1, index + 1);
                    return;
                }
            }
        }

        input.setSelectionRange(value.length, value.length);
    };

    const handlePhoneDeletion = (input, key) => {
        const start = input.selectionStart ?? 0;
        const end = input.selectionEnd ?? start;
        const rawDigits = extractPhoneDigits(input.value);
        const prefixDigits = extractPhoneDigits(input.value.slice(0, start)).length;
        const selectedDigits = extractPhoneDigits(input.value.slice(start, end)).length;

        let digits = rawDigits;
        let cursorDigitIndex = prefixDigits;

        if (start !== end) {
            if (!selectedDigits) {
                return false;
            }
            const from = prefixDigits - selectedDigits;
            digits = `${rawDigits.slice(0, from)}${rawDigits.slice(prefixDigits)}`;
            cursorDigitIndex = from;
        } else if (key === 'Backspace') {
            if (prefixDigits <= 1) {
                return true;
            }
            digits = `${rawDigits.slice(0, prefixDigits - 1)}${rawDigits.slice(prefixDigits)}`;
            cursorDigitIndex = prefixDigits - 1;
        } else {
            if (prefixDigits >= rawDigits.length) {
                return true;
            }
            digits = `${rawDigits.slice(0, prefixDigits)}${rawDigits.slice(prefixDigits + 1)}`;
            cursorDigitIndex = prefixDigits;
        }

        input.value = formatPhoneDigits(digits);
        setCursorByDigitIndex(input, cursorDigitIndex);
        return true;
    };

    const getCsrfToken = (form) => {
        const tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
        return tokenInput ? tokenInput.value : '';
    };

    const getFieldContainer = (field) => {
        if (!field) {
            return null;
        }
        return field.closest('.field, .form-consent');
    };

    const clearFieldErrors = (form) => {
        form.querySelectorAll('[data-generated-error]').forEach((node) => node.remove());
        form.querySelectorAll('.field.field-error').forEach((node) => node.classList.remove('field-error'));
        form.querySelectorAll('.form-consent--error').forEach((node) => node.classList.remove('form-consent--error'));
    };

    const renderStatus = (form, messages, type) => {
        const statusBox = form.querySelector('[data-form-status]');
        if (!statusBox) {
            return;
        }

        const items = Array.isArray(messages) ? messages : [messages];

        statusBox.replaceChildren(
            ...items
                .filter(Boolean)
                .map((message) => {
                    const banner = document.createElement('div');
                    banner.className = `notice-banner notice-banner--${type}`;
                    banner.textContent = message;
                    return banner;
                }),
        );
        statusBox.hidden = statusBox.childElementCount === 0;
    };

    const appendFieldError = (field, message) => {
        if (!field || !message) {
            return;
        }

        const container = getFieldContainer(field);
        if (!container) {
            return;
        }

        if (container.classList.contains('form-consent')) {
            container.classList.add('form-consent--error');
        } else {
            container.classList.add('field-error');
        }

        const errorNode = document.createElement('span');
        errorNode.className = 'field-help';
        if (container.classList.contains('form-consent')) {
            errorNode.classList.add('field-help--block');
        }
        errorNode.dataset.generatedError = 'true';
        errorNode.textContent = message;
        container.insertAdjacentElement('beforeend', errorNode);
    };

    const renderServerErrors = (form, errors) => {
        const summary = [];

        Object.entries(errors || {}).forEach(([fieldName, messages]) => {
            const items = (messages || []).filter(Boolean);
            if (!items.length) {
                return;
            }

            if (fieldName === '__all__' || fieldName === 'non_field_errors') {
                summary.push(...items);
                return;
            }

            appendFieldError(form.querySelector(`[name="${fieldName}"]`), items[0]);
            summary.push(...items);
        });

        renderStatus(form, summary, 'error');
    };

    const setLoadingState = (button, isLoading) => {
        if (!button) {
            return;
        }
        button.disabled = isLoading;
        button.classList.toggle('is-loading', isLoading);
        button.setAttribute('aria-busy', String(isLoading));
    };

    const validateName = (input) => {
        const value = (input.value || '').trim().replace(/\s+/g, ' ');
        const lettersCount = (value.match(/[A-Za-zА-Яа-яЁё]/g) || []).length;
        const digitsCount = (value.match(/\d/g) || []).length;

        if (value.length < 2) {
            input.setCustomValidity('Укажите имя не короче 2 символов.');
        } else if (value.length > 80) {
            input.setCustomValidity('Имя должно быть не длиннее 80 символов.');
        } else if (lettersCount < 2 || digitsCount > 3 || hasLink(value)) {
            input.setCustomValidity('Укажите реальное имя без ссылок.');
        } else {
            input.setCustomValidity('');
        }

        input.value = value;
    };

    const validatePhone = (input) => {
        normalizePhoneInput(input);
        const digits = input.value.replace(/\D/g, '');

        if (digits.length !== 11 || !digits.startsWith('7')) {
            input.setCustomValidity('Укажите телефон в формате +7XXXXXXXXXX.');
        } else {
            input.setCustomValidity('');
        }
    };

    const validateComment = (input) => {
        const value = (input.value || '').trim();

        if (value.length > 1000) {
            input.setCustomValidity('Комментарий должен быть не длиннее 1000 символов.');
        } else if (hasLink(value)) {
            input.setCustomValidity('Ссылки в комментарии запрещены.');
        } else {
            input.setCustomValidity('');
        }
    };

    document.querySelectorAll('[data-application-form]').forEach((form) => {
        const nameInput = form.querySelector('input[name="name"]');
        const phoneInput = form.querySelector('input[name="phone"]');
        const commentInput = form.querySelector('textarea[name="comment"]');

        if (nameInput) {
            nameInput.addEventListener('input', () => validateName(nameInput));
            nameInput.addEventListener('blur', () => validateName(nameInput));
        }

        if (phoneInput) {
            phoneInput.addEventListener('focus', () => {
                if (!phoneInput.value.trim()) {
                    phoneInput.value = '+7 ';
                }
            });
            phoneInput.addEventListener('keydown', (event) => {
                if (event.key !== 'Backspace' && event.key !== 'Delete') {
                    return;
                }
                if (!/\D/.test(phoneInput.value)) {
                    return;
                }
                if (!handlePhoneDeletion(phoneInput, event.key)) {
                    return;
                }
                event.preventDefault();
                validatePhone(phoneInput);
            });
            phoneInput.addEventListener('input', () => validatePhone(phoneInput));
            phoneInput.addEventListener('blur', () => validatePhone(phoneInput));
        }

        if (commentInput) {
            commentInput.addEventListener('input', () => validateComment(commentInput));
            commentInput.addEventListener('blur', () => validateComment(commentInput));
        }

        form.addEventListener('submit', async (event) => {
            if (nameInput) {
                validateName(nameInput);
            }
            if (phoneInput) {
                validatePhone(phoneInput);
            }
            if (commentInput) {
                validateComment(commentInput);
            }

            if (!form.checkValidity()) {
                event.preventDefault();
                form.reportValidity();
                return;
            }

            event.preventDefault();
            clearFieldErrors(form);
            renderStatus(form, [], 'success');

            const submitButton = form.querySelector('button[type="submit"]');
            setLoadingState(submitButton, true);

            try {
                const response = await fetch(form.dataset.applicationEndpoint || form.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(form),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: new FormData(form),
                });
                const payload = await response.json();

                if (!response.ok) {
                    renderServerErrors(form, payload.errors);
                    return;
                }

                form.reset();
                renderStatus(form, payload.message || 'Спасибо! Мы скоро свяжемся с вами.', 'success');
            } catch (error) {
                renderStatus(form, 'Не удалось отправить заявку. Попробуйте еще раз.', 'error');
            } finally {
                setLoadingState(submitButton, false);
            }
        });
    });
})();

(() => {
    const galleries = document.querySelectorAll('[data-product-detail-gallery]');

    if (!galleries.length) {
        return;
    }

    galleries.forEach((gallery) => {
        const track = gallery.querySelector('[data-detail-gallery-track]');
        const previousButton = gallery.querySelector('[data-detail-gallery-prev]');
        const nextButton = gallery.querySelector('[data-detail-gallery-next]');
        const thumbs = [...gallery.querySelectorAll('[data-detail-gallery-thumb]')];
        const slideCount = Number.parseInt(gallery.dataset.galleryLength || '0', 10);

        if (!track || slideCount <= 0) {
            return;
        }

        const update = (nextIndex) => {
            const normalizedIndex = ((nextIndex % slideCount) + slideCount) % slideCount;
            gallery.dataset.galleryIndex = String(normalizedIndex);
            track.style.transform = `translateX(-${normalizedIndex * 100}%)`;
            thumbs.forEach((thumb, index) => {
                thumb.classList.toggle('is-active', index === normalizedIndex);
            });
        };

        thumbs.forEach((thumb) => {
            thumb.addEventListener('click', () => {
                update(Number.parseInt(thumb.dataset.index || '0', 10));
                thumb.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' });
            });
        });

        if (previousButton) {
            previousButton.addEventListener('click', () => update(Number.parseInt(gallery.dataset.galleryIndex || '0', 10) - 1));
        }

        if (nextButton) {
            nextButton.addEventListener('click', () => update(Number.parseInt(gallery.dataset.galleryIndex || '0', 10) + 1));
        }

        update(0);
    });
})();
