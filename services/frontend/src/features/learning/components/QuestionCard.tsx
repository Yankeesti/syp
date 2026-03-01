import { useState, useEffect, useRef } from 'react';
import { Eye, Check, X, ChevronRight, ChevronLeft, XCircle } from 'lucide-react';
import type { Question } from '../../quiz/entities/question/types';

interface QuestionCardProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
  onAnswer: (answer: QuestionAnswer, autoAdvance?: boolean) => void;
  onCancel: () => void;
  onPrevious?: () => void;
  onNext?: () => void;
  onSaveTemporary?: (questionId: string, answer: QuestionAnswer) => void;
  onLoadTemporary?: (questionId: string) => QuestionAnswer | undefined;
  isAnswerSaved?: boolean;
  isComplete: boolean;
}

export type QuestionAnswer =
  | {
      type: 'multiple-choice';
      selectedOptionIndexes: number[];
    }
  | {
      type: 'freitext';
      textResponse: string;
      isCorrect: boolean;
    }
  | {
      type: 'lueckentext';
      filledWords: string[];
    };

export function QuestionCard({ question, questionNumber, totalQuestions, onAnswer, onCancel, onPrevious, onNext, onSaveTemporary, onLoadTemporary, isAnswerSaved = false, isComplete }: QuestionCardProps) {
  const [showSolution, setShowSolution] = useState(false);
  const [userAnswer, setUserAnswer] = useState('');
  const [selectedOptions, setSelectedOptions] = useState<number[]>([]);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [isFreitextConfirmed, setIsFreitextConfirmed] = useState(false);
  const [isLueckentextConfirmed, setIsLueckentextConfirmed] = useState(false);
  const [filledWords, setFilledWords] = useState<(string | null)[]>([]);
  const [availableWords, setAvailableWords] = useState<string[]>([]);
  const isInitialLoadRef = useRef(true);
  const lastQuestionIdRef = useRef<string | null>(null);

  const stripBraces = (text: string) => text.replace(/[{}]/g, '');

  // Save current answer before navigation
  const saveCurrentAnswer = () => {
    if (!onSaveTemporary) return;
    
    if (question.type === 'multiple-choice') {
      if (selectedOptions.length > 0) {
        onSaveTemporary(question.id, {
          type: 'multiple-choice',
          selectedOptionIndexes: [...selectedOptions],
        });
      } else {
        // Explicitly clear saved answer if nothing is selected
        // We need to save empty array to override previous selection
        onSaveTemporary(question.id, {
          type: 'multiple-choice',
          selectedOptionIndexes: [],
        });
      }
    } else if (question.type === 'freitext') {
      if (userAnswer.trim()) {
        onSaveTemporary(question.id, {
          type: 'freitext',
          textResponse: userAnswer,
          isCorrect: false, // Will be set when confirmed
        });
      }
    } else if (question.type === 'lueckentext') {
      // Always save, even if empty, to preserve confirmation state
      if (filledWords.some(w => w !== null && w.trim() !== '')) {
        // Only save if at least one word is filled (not null and not empty string)
        onSaveTemporary(question.id, {
          type: 'lueckentext',
          filledWords: filledWords.map(w => (w !== null && w.trim() !== '') ? w : ''),
        });
      } else {
        // Explicitly clear saved answer if nothing is filled
        // Save empty array to override previous selection
        onSaveTemporary(question.id, {
          type: 'lueckentext',
          filledWords: [],
        });
      }
    }
  };

  // Load saved answer when question changes (only when question ID actually changes)
  useEffect(() => {
    if (!onLoadTemporary) return;
    
    // Only load if question ID actually changed
    if (lastQuestionIdRef.current === question.id) {
      return;
    }
    
    lastQuestionIdRef.current = question.id;
    isInitialLoadRef.current = true;
    
    const savedAnswer = onLoadTemporary(question.id);
    
    if (savedAnswer) {
      if (question.type === 'multiple-choice' && savedAnswer.type === 'multiple-choice') {
        // Load saved selection, even if empty (to clear previous selection)
        setSelectedOptions([...savedAnswer.selectedOptionIndexes]);
        // Für die letzte Frage immer neu bestätigen lassen
        setIsConfirmed(isAnswerSaved && questionNumber < totalQuestions);
      } else if (question.type === 'freitext' && savedAnswer.type === 'freitext') {
        setUserAnswer(savedAnswer.textResponse);
        setIsFreitextConfirmed(isAnswerSaved && questionNumber < totalQuestions);
        setShowSolution(false);
      } else if (question.type === 'lueckentext' && savedAnswer.type === 'lueckentext') {
        // If empty array, clear all selections
        if (savedAnswer.filledWords.length === 0) {
          setFilledWords(new Array(question.correctWords.length).fill(null));
          setAvailableWords([...question.words]);
          setIsLueckentextConfirmed(false);
        } else {
          // Convert empty strings back to null, only keep non-empty strings
          // Ensure we have the correct length
          const expectedLength = question.correctWords.length;
          const filled = new Array(expectedLength).fill(null).map((_, index) => {
            if (index < savedAnswer.filledWords.length) {
              const word = savedAnswer.filledWords[index];
              return (word && word.trim() !== '') ? word : null;
            }
            return null;
          });
          
          // Check if there are any actual filled words (not all null)
          const hasFilledWords = filled.some(w => w !== null && w.trim() !== '');
          
          if (hasFilledWords) {
            setFilledWords(filled);
            // Restore available words - only words that are actually filled (not null)
            const usedWords = filled.filter(w => w !== null && w.trim() !== '') as string[];
            setAvailableWords(question.words.filter(w => !usedWords.includes(w)));
            // If answer is saved on server, it means it was confirmed
            // Also check if all blanks are filled - if yes, assume it was confirmed
            const allFilled = filled.length === expectedLength && 
                             filled.every(w => w !== null && w.trim() !== '');
            setIsLueckentextConfirmed(
              (isAnswerSaved || allFilled) && questionNumber < totalQuestions,
            );
          } else {
            // If all words are empty, treat as no saved answer
            setFilledWords(new Array(expectedLength).fill(null));
            setAvailableWords([...question.words]);
            setIsLueckentextConfirmed(false);
          }
        }
      }
    } else {
      // Reset if no saved answer
      setSelectedOptions([]);
      setUserAnswer('');
      // Für neue/ungespeicherte Antworten nie automatisch als bestätigt markieren
      setIsConfirmed(false);
      setIsFreitextConfirmed(false);
      setIsLueckentextConfirmed(false);
      setShowSolution(false);
      if (question.type === 'lueckentext') {
        setFilledWords(new Array(question.correctWords.length).fill(null));
        setAvailableWords([...question.words]);
      }
    }
    
    isInitialLoadRef.current = false;
  }, [
    question.id,
    question.type,
    questionNumber,
    question.type === 'lueckentext' ? question.words : undefined,
    question.type === 'lueckentext' ? question.correctWords : undefined,
    isAnswerSaved,
    onLoadTemporary,
  ]);

  // Auto-save answers when they change (with debounce to prevent too frequent saves)
  useEffect(() => {
    if (!onSaveTemporary || isInitialLoadRef.current) return;
    
    const timeoutId = setTimeout(() => {
      if (question.type === 'multiple-choice') {
        // Always save, even if empty, to clear previous selection
        onSaveTemporary(question.id, {
          type: 'multiple-choice',
          selectedOptionIndexes: [...selectedOptions],
        });
      } else if (question.type === 'freitext' && userAnswer.trim()) {
        onSaveTemporary(question.id, {
          type: 'freitext',
          textResponse: userAnswer,
          isCorrect: false,
        });
      } else if (question.type === 'lueckentext') {
        if (filledWords.some(w => w !== null && w.trim() !== '')) {
          // Only save if at least one word is filled (not null and not empty string)
          onSaveTemporary(question.id, {
            type: 'lueckentext',
            filledWords: filledWords.map(w => (w !== null && w.trim() !== '') ? w : ''),
          });
        } else {
          // Save empty array to clear previous selection
          onSaveTemporary(question.id, {
            type: 'lueckentext',
            filledWords: [],
          });
        }
      }
    }, 300); // Debounce 300ms
    
    return () => clearTimeout(timeoutId);
  }, [question.id, question.type, selectedOptions, userAnswer, filledWords, onSaveTemporary]);

  if (isComplete) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="mb-2 text-slate-900">Test abgeschlossen!</h2>
        <p className="text-slate-600">Deine Ergebnisse wurden gespeichert.</p>
      </div>
    );
  }

  const handleMultipleChoiceConfirm = async () => {
    if (selectedOptions.length === 0) return;
    // Save answer to server immediately, but don't auto-advance
    const answer: QuestionAnswer = {
      type: 'multiple-choice',
      selectedOptionIndexes: [...selectedOptions],
    };
    onSaveTemporary?.(question.id, answer);
    
    try {
      await onAnswer(answer, false); // false = don't auto-advance to next question
      // Nur bestätigen, Test nicht automatisch beenden
      setIsConfirmed(true);
    } catch (error) {
      console.error('Failed to save answer', error);
      alert('Antwort konnte nicht gespeichert werden.');
    }
    // Note: User can still change selection after confirmation
  };

  const handleFreitextAnswer = async (isCorrect: boolean) => {
    const answer: QuestionAnswer = {
      type: 'freitext',
      textResponse: userAnswer,
      isCorrect,
    };
    onSaveTemporary?.(question.id, answer);
    
    try {
      await onAnswer(answer, false); // false = don't auto-advance to next question
      // Nur bestätigen, Test nicht automatisch beenden
      setIsFreitextConfirmed(true);
    } catch (error) {
      console.error('Failed to save answer', error);
      alert('Antwort konnte nicht gespeichert werden.');
    }
    setShowSolution(false);
  };

  const handleFreitextNext = () => {
    if (question.type !== 'freitext') return;
    const answer: QuestionAnswer = {
      type: 'freitext',
      textResponse: userAnswer,
      isCorrect: false, // Will be set when confirmed
    };
    onSaveTemporary?.(question.id, answer);
    onAnswer(answer, false);
    onNext?.();
  };

  const handleLueckentextWordClick = (word: string, index: number) => {
    // Find first empty slot
    const emptyIndex = filledWords.findIndex(w => w === null);
    if (emptyIndex !== -1) {
      const newFilled = [...filledWords];
      newFilled[emptyIndex] = word;
      setFilledWords(newFilled);
      
      const newAvailable = availableWords.filter((_, i) => i !== index);
      setAvailableWords(newAvailable);
      
      // Reset confirmation if user changes selection
      if (isLueckentextConfirmed) {
        setIsLueckentextConfirmed(false);
      }
    }
  };

  const handleLueckentextRemove = (index: number) => {
    const word = filledWords[index];
    if (word) {
      const newFilled = [...filledWords];
      newFilled[index] = null;
      setFilledWords(newFilled);
      
      setAvailableWords([...availableWords, word]);
      
      // Reset confirmation if user changes selection
      if (isLueckentextConfirmed) {
        setIsLueckentextConfirmed(false);
      }
    }
  };

  const handleLueckentextConfirm = async () => {
    if (question.type !== 'lueckentext') return;
    const filled = filledWords.map((word) => word ?? '');
    const answer: QuestionAnswer = { type: 'lueckentext', filledWords: filled };
    onSaveTemporary?.(question.id, answer);
    
    try {
      await onAnswer(answer, false); // false = don't auto-advance to next question
      // Nur bestätigen, Test nicht automatisch beenden
      setIsLueckentextConfirmed(true);
    } catch (error) {
      console.error('Failed to save answer', error);
      alert('Antwort konnte nicht gespeichert werden.');
    }
  };

  const handleLueckentextNext = () => {
    if (question.type !== 'lueckentext') return;
    const filled = filledWords.map((word) => word ?? '');
    const answer: QuestionAnswer = { type: 'lueckentext', filledWords: filled };
    onSaveTemporary?.(question.id, answer);
    onAnswer(answer, false);
    onNext?.();
  };

  const handlePrevious = () => {
    saveCurrentAnswer();
    onPrevious?.();
  };

  const handleNext = () => {
    saveCurrentAnswer();
    onNext?.();
  };

  const handleFinishTest = () => {
    // Answer is already saved in the confirm handlers, just finalize the attempt
    onCancel(); // This will finalize the attempt
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">
              Frage {questionNumber} von {totalQuestions}
            </span>
            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md">
              {question.theme}
            </span>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Navigation Buttons - Top (only arrows) */}
            {onPrevious && questionNumber > 1 && (
              <button
                type="button"
                onClick={handlePrevious}
                className="flex items-center justify-center p-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                title="Zurück"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            )}
            
            {onNext && questionNumber < totalQuestions && (
              <button
                type="button"
                onClick={handleNext}
                className="flex items-center justify-center p-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                title="Weiter"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            )}
            
            {question.type === 'freitext' && (
              <button
                type="button"
                onClick={() => setShowSolution(!showSolution)}
                className="flex items-center gap-2 px-4 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <Eye className="w-4 h-4" />
                {showSolution ? 'Lösung verbergen' : 'Lösung anzeigen'}
              </button>
            )}
          </div>
        </div>
        
        <div className="mb-6">
          <h3 className="mb-3 text-slate-700">
            {question.type === 'multiple-choice' && 'Multiple Choice:'}
            {question.type === 'freitext' && 'Freitextfrage:'}
            {question.type === 'lueckentext' && 'Lückentext:'}
          </h3>
          
          {question.type === 'multiple-choice' && (
            <p className="text-slate-900 leading-relaxed mb-6">{question.question}</p>
          )}
          
          {question.type === 'freitext' && (
            <p className="text-slate-900 leading-relaxed">{question.question}</p>
          )}
          
          {question.type === 'lueckentext' && (
            <div className="text-slate-900 leading-relaxed">
              <p className="mb-4">Fülle die Lücken mit den richtigen Wörtern:</p>
              <div className="p-4 bg-slate-50 rounded-lg">
                {question.textParts.map((part, index) => (
                  <span key={index}>
                    {stripBraces(part)}
                    {index < question.textParts.length - 1 && (
                      <button
                        type="button"
                        onClick={() => handleLueckentextRemove(index)}
                        className={`inline-flex items-center justify-center min-w-[120px] mx-1 px-3 py-1 rounded border-2 ${
                          filledWords[index]
                            ? 'bg-blue-50 border-blue-300 text-blue-700'
                            : 'bg-white border-dashed border-slate-300 text-slate-400'
                        }`}
                      >
                        {filledWords[index] || '___'}
                      </button>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {question.type === 'freitext' && showSolution && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="mb-2 text-green-900">Musterlösung:</h4>
            <p className="text-green-800 leading-relaxed">{question.solution}</p>
          </div>
        )}
      </div>
      
      {/* Multiple Choice Options */}
      {question.type === 'multiple-choice' && (
        <div className="mb-6 space-y-3">
          {question.options.map((option, index) => {
            const isSelected = selectedOptions.includes(index);

            return (
              <button
                key={index}
                onClick={() => {
                  // Allow changes even after confirmation
                  setSelectedOptions((prev) => {
                    const newSelection = prev.includes(index)
                      ? prev.filter(i => i !== index)
                      : [...prev, index];
                    
                    // If answer was previously confirmed and saved, save new answer immediately
                    if (isConfirmed && isAnswerSaved && newSelection.length > 0) {
                      const answer: QuestionAnswer = {
                        type: 'multiple-choice',
                        selectedOptionIndexes: [...newSelection],
                      };
                      onSaveTemporary?.(question.id, answer);
                      onAnswer(answer, false);
                    }
                    
                    return newSelection;
                  });
                  // Reset confirmation state when user changes selection
                  if (isConfirmed) {
                    setIsConfirmed(false);
                  }
                }}
                className={`w-full flex items-center justify-between p-4 rounded-lg border-2 transition-all text-left ${
                  isSelected
                    ? 'bg-blue-50 border-blue-500'
                    : 'bg-white border-slate-200 hover:border-slate-300'
                } ${isConfirmed ? 'cursor-default' : 'cursor-pointer'}`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                      isSelected
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-slate-400'
                    }`}
                  >
                    {isSelected && (
                      <Check className="w-3 h-3 text-white" />
                    )}
                  </div>
                  <span className="text-slate-900">{option}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
      
      {/* Freitext Answer */}
      {question.type === 'freitext' && (
        <div className="mb-6">
          <h3 className="mb-3 text-slate-700">Antwort:</h3>
          <textarea
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            placeholder="Gib hier deine Antwort ein..."
            className="w-full h-32 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
        </div>
      )}
      
      {/* Lückentext Words */}
          {question.type === 'lueckentext' && (
            <div className="mb-6">
          <h3 className="mb-3 text-slate-700">Verfügbare Wörter:</h3>
          <div className="flex flex-wrap gap-2">
            {availableWords.map((word, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleLueckentextWordClick(word, index)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-900 rounded-lg border border-slate-300 transition-colors"
              >
                {word}
              </button>
            ))}
          </div>
        </div>
      )}
      
      {/* Action Buttons */}
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="flex items-center justify-center gap-2 px-6 py-3 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
        >
          <XCircle className="w-5 h-5" />
          Abbrechen
        </button>
        
        <div className="flex items-center gap-3">
          {/* Answer Buttons */}
          {question.type === 'multiple-choice' && !isConfirmed && (
            <button
              type="button"
              onClick={handleMultipleChoiceConfirm}
              disabled={selectedOptions.length === 0}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
              style={{ backgroundColor: '#2563eb', color: '#ffffff', border: '2px solid #1d4ed8', fontSize: 14 }}
            >
              Bestätigen
            </button>
          )}
          
          {question.type === 'multiple-choice' && isConfirmed && questionNumber < totalQuestions && (
            <button
              type="button"
              onClick={handleNext}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Weiter
              <ChevronRight className="w-5 h-5" />
            </button>
          )}
          
          {question.type === 'freitext' && !isFreitextConfirmed && (
            <>
              <button
                type="button"
                onClick={() => handleFreitextAnswer(true)}
                disabled={!userAnswer.trim()}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
              >
                <Check className="w-5 h-5" />
                Richtig
              </button>
              
              <button
                type="button"
                onClick={() => handleFreitextAnswer(false)}
                disabled={!userAnswer.trim()}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
              >
                <X className="w-5 h-5" />
                Falsch
              </button>
            </>
          )}
          
          {question.type === 'freitext' && isFreitextConfirmed && questionNumber < totalQuestions && (
            <button
              type="button"
              onClick={handleFreitextNext}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Weiter
              <ChevronRight className="w-5 h-5" />
            </button>
          )}
          
          {question.type === 'lueckentext' && !isLueckentextConfirmed && (
            <button
              type="button"
              onClick={handleLueckentextConfirm}
              disabled={filledWords.some(w => w === null)}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              Bestätigen
            </button>
          )}
          
          {question.type === 'lueckentext' && isLueckentextConfirmed && questionNumber < totalQuestions && (
            <button
              type="button"
              onClick={handleLueckentextNext}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Weiter
              <ChevronRight className="w-5 h-5" />
            </button>
          )}

          {/* Separate Finish-Button nur auf der letzten Frage
              und nur, wenn die aktuelle Frage bestätigt wurde,
              damit kein leerer zusätzlicher Action-Button erscheint. */}
          {questionNumber === totalQuestions &&
            ((question.type === 'multiple-choice' && isConfirmed) ||
              (question.type === 'freitext' && isFreitextConfirmed) ||
              (question.type === 'lueckentext' && isLueckentextConfirmed)) && (
              <button
                type="button"
                onClick={handleFinishTest}
                className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg transition-colors"
                style={{
                  backgroundColor: '#16a34a',
                  color: '#ffffff',
                  border: '2px solid #15803d',
                  fontSize: 14,
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                }}
              >
                <Check className="w-5 h-5" />
                Test abschließen
              </button>
            )}
        </div>
      </div>
    </div>
  );
}
