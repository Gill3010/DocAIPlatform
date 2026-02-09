import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, ArrowRight } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { DashboardConversionType, ConversionCategory } from '../../constants/conversions';
import { CONVERSION_CATEGORY_LABELS } from '../../constants/conversions';
import './ConversionSearch.css';

const CATEGORY_GRADIENT: Record<ConversionCategory, string> = {
    document: 'gradient-primary',
    image: 'gradient-info',
    web: 'gradient-warm'
};

const MAX_VISIBLE_RESULTS = 10;

const TYPEWRITER_PHRASE = 'Buscar conversión: PDF a Word, Word, documento…';
const TYPE_SPEED_MS = 80;
const ERASE_SPEED_MS = 40;
const PAUSE_AFTER_TYPE_MS = 2000;
const PAUSE_AFTER_ERASE_MS = 600;

interface ConversionSearchProps {
    query: string;
    onQueryChange: (value: string) => void;
    filteredConversions: DashboardConversionType[];
    inputId?: string;
    listboxId?: string;
}

export const ConversionSearch = ({
    query,
    onQueryChange,
    filteredConversions,
    inputId = 'conversion-search-input',
    listboxId = 'conversion-search-listbox'
}: ConversionSearchProps) => {
    const navigate = useNavigate();
    const [highlightedIndex, setHighlightedIndex] = useState(-1);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [typewriterText, setTypewriterText] = useState('');
    const [typewriterPhase, setTypewriterPhase] = useState<'typing' | 'pause' | 'erasing'>('typing');
    const [isInputFocused, setIsInputFocused] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const listboxRef = useRef<HTMLUListElement>(null);

    const showDropdown = query.trim().length >= 1 && isDropdownOpen;
    const displayResults = filteredConversions.slice(0, MAX_VISIBLE_RESULTS);
    const hasMore = filteredConversions.length > MAX_VISIBLE_RESULTS;

    useEffect(() => {
        setHighlightedIndex(-1);
    }, [query]);

    useEffect(() => {
        if (highlightedIndex >= 0 && listboxRef.current) {
            const item = listboxRef.current.children[highlightedIndex] as HTMLElement;
            item?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }, [highlightedIndex]);

    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setIsDropdownOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Efecto máquina de escribir en el placeholder (solo cuando el input está vacío y sin foco)
    useEffect(() => {
        if (query.length > 0 || isInputFocused) return;

        const fullLength = TYPEWRITER_PHRASE.length;
        let timeoutId: ReturnType<typeof setTimeout>;

        if (typewriterPhase === 'typing') {
            const currentLen = typewriterText.length;
            const nextLength = Math.min(currentLen + 1, fullLength);
            timeoutId = setTimeout(() => {
                setTypewriterText(TYPEWRITER_PHRASE.slice(0, nextLength));
                if (nextLength >= fullLength) setTypewriterPhase('pause');
            }, TYPE_SPEED_MS);
        } else if (typewriterPhase === 'pause') {
            timeoutId = setTimeout(() => setTypewriterPhase('erasing'), PAUSE_AFTER_TYPE_MS);
        } else {
            const currentLen = typewriterText.length;
            const nextLength = Math.max(currentLen - 1, 0);
            timeoutId = setTimeout(() => {
                setTypewriterText(TYPEWRITER_PHRASE.slice(0, nextLength));
                if (nextLength === 0) setTypewriterPhase('typing');
            }, nextLength === 0 ? PAUSE_AFTER_ERASE_MS : ERASE_SPEED_MS);
        }

        return () => clearTimeout(timeoutId);
    }, [query.length, isInputFocused, typewriterPhase, typewriterText]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!showDropdown || displayResults.length === 0) {
            if (e.key === 'Escape') {
                onQueryChange('');
                setIsDropdownOpen(false);
            }
            return;
        }
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setHighlightedIndex((i) => (i < displayResults.length - 1 ? i + 1 : 0));
                break;
            case 'ArrowUp':
                e.preventDefault();
                setHighlightedIndex((i) => (i <= 0 ? displayResults.length - 1 : i - 1));
                break;
            case 'Enter':
                e.preventDefault();
                if (highlightedIndex >= 0 && displayResults[highlightedIndex]) {
                    const conv = displayResults[highlightedIndex];
                    navigate(`/convert?from=${encodeURIComponent(conv.primarySourceFormat)}&to=${encodeURIComponent(conv.targetId)}`);
                    setIsDropdownOpen(false);
                }
                break;
            case 'Escape':
                e.preventDefault();
                onQueryChange('');
                setIsDropdownOpen(false);
                setHighlightedIndex(-1);
                break;
            default:
                break;
        }
    };

    return (
        <div ref={containerRef} className="conversion-search">
            <div className="conversion-search__input-wrapper">
                <Search
                    size={20}
                    className="conversion-search__icon"
                    aria-hidden
                />
                <input
                    id={inputId}
                    type="search"
                    className="conversion-search__input"
                    placeholder={query.length > 0 ? '' : typewriterText || ' '}
                    value={query}
                    onChange={(e) => {
                        onQueryChange(e.target.value);
                        setIsDropdownOpen(true);
                    }}
                    onFocus={() => {
                        setIsInputFocused(true);
                        if (query.trim().length >= 1) setIsDropdownOpen(true);
                    }}
                    onBlur={() => setIsInputFocused(false)}
                    onKeyDown={handleKeyDown}
                    autoComplete="off"
                    autoCorrect="off"
                    autoCapitalize="off"
                    spellCheck={false}
                    aria-label="Buscar tipo de conversión"
                    aria-expanded={showDropdown}
                    aria-controls={listboxId}
                    aria-activedescendant={
                        showDropdown && highlightedIndex >= 0 && displayResults[highlightedIndex]
                            ? `${listboxId}-item-${highlightedIndex}`
                            : undefined
                    }
                />
            </div>

            {showDropdown && (
                <div className="conversion-search__dropdown" role="presentation">
                    {displayResults.length > 0 ? (
                        <ul
                            id={listboxId}
                            ref={listboxRef}
                            className="conversion-search__listbox"
                            role="listbox"
                        >
                            {displayResults.map((conv, index) => {
                                const Icon = conv.icon as LucideIcon;
                                const href = `/convert?from=${encodeURIComponent(conv.primarySourceFormat)}&to=${encodeURIComponent(conv.targetId)}`;
                                const isHighlighted = index === highlightedIndex;
                                return (
                                    <li
                                        key={conv.id}
                                        id={`${listboxId}-item-${index}`}
                                        role="option"
                                        aria-selected={isHighlighted}
                                        className={`conversion-search__result ${isHighlighted ? 'conversion-search__result--highlighted' : ''}`}
                                        onMouseEnter={() => setHighlightedIndex(index)}
                                    >
                                        <Link
                                            to={href}
                                            className="conversion-search__result-link"
                                            onClick={() => setIsDropdownOpen(false)}
                                        >
                                            <span className={`conversion-search__result-icon ${CATEGORY_GRADIENT[conv.category]}`}>
                                                <Icon size={18} strokeWidth={2} />
                                            </span>
                                            <span className="conversion-search__result-label">
                                                {conv.sourceLabel}
                                                <ArrowRight size={14} className="conversion-search__result-arrow" aria-hidden />
                                                {conv.targetLabel}
                                            </span>
                                            <span className="conversion-search__result-category">
                                                {CONVERSION_CATEGORY_LABELS[conv.category]}
                                            </span>
                                        </Link>
                                    </li>
                                );
                            })}
                        </ul>
                    ) : (
                        <div className="conversion-search__empty" role="status">
                            No hay coincidencias. Prueba con «PDF», «Word» o «imagen».
                        </div>
                    )}
                    {hasMore && displayResults.length > 0 && (
                        <div className="conversion-search__more">
                            {filteredConversions.length} resultados
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
