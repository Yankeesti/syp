import { useState, useMemo } from 'react';
import { ArrowLeft, Save, Plus, Trash2, GripVertical, Undo2, Eye, EyeOff, Check, AlertCircle } from 'lucide-react';
import { Button } from '../../../shared/ui/button';
import { Input } from '../../../shared/ui/input';
import { Textarea } from '../../../shared/ui/textarea';
import { Label } from '../../../shared/ui/label';
import { Checkbox } from '../../../shared/ui/checkbox';
import { Badge } from '../../../shared/ui/badge';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../../../shared/ui/card';
import type { Question, LueckentextQuestion } from '../entities/question/types';

// =============================================================================
// Cloze Text Helper Functions
// =============================================================================

/**
 * Konvertiert textParts und correctWords zu einem Raw-Text mit {{Syntax}}
 * Beispiel: ["Bei ", " handelt..."], ["Test"] → "Bei {{Test}} handelt..."
 */
function toRawText(textParts: string[], correctWords: string[]): string {
  let result = '';
  for (let i = 0; i < textParts.length; i++) {
    result += textParts[i];
    if (i < correctWords.length) {
      result += `{{${correctWords[i]}}}`;
    }
  }
  return result;
}

/**
 * Parst einen Raw-Text mit {{Syntax}} zu textParts und correctWords
 * Beispiel: "Bei {{Test}} handelt..." → { textParts: ["Bei ", " handelt..."], correctWords: ["Test"] }
 */
function parseRawText(rawText: string): { textParts: string[]; correctWords: string[] } {
  const regex = /\{\{([^}]+)\}\}/g;
  const textParts: string[] = [];
  const correctWords: string[] = [];

  let lastIndex = 0;
  let match;

  while ((match = regex.exec(rawText)) !== null) {
    // Text vor der Lücke
    textParts.push(rawText.slice(lastIndex, match.index));
    // Das Wort in der Lücke
    correctWords.push(match[1]);
    lastIndex = regex.lastIndex;
  }

  // Restlicher Text nach der letzten Lücke
  textParts.push(rawText.slice(lastIndex));

  return { textParts, correctWords };
}

// =============================================================================
// Cloze Editor Component
// =============================================================================

interface ClozeEditorProps {
  question: LueckentextQuestion;
  index: number;
  isDeleted: boolean;
  onUpdate: (question: LueckentextQuestion) => void;
  onDelete: () => void;
  onUndoDelete: () => void;
}

function ClozeEditor({ question, index, isDeleted, onUpdate, onDelete, onUndoDelete }: ClozeEditorProps) {
  // Lokaler State für den Raw-Text
  const [rawText, setRawText] = useState(() => toRawText(question.textParts, question.correctWords));
  const [showSolution, setShowSolution] = useState(true);

  // Parse den aktuellen Text für die Vorschau
  const parsed = useMemo(() => parseRawText(rawText), [rawText]);
  const gapCount = parsed.correctWords.length;
  const hasValidGaps = gapCount > 0;

  // Handler für Textänderungen
  const handleTextChange = (newRawText: string) => {
    setRawText(newRawText);

    const { textParts, correctWords } = parseRawText(newRawText);

    // Behalte blankIds wenn die Anzahl der Lücken gleich bleibt
    let blankIds = question.blankIds;
    if (blankIds && blankIds.length !== correctWords.length) {
      // Anzahl hat sich geändert - IDs werden beim Speichern neu generiert
      blankIds = undefined;
    }

    onUpdate({
      ...question,
      textParts,
      correctWords,
      words: correctWords, // words wird für Quiz-Anzeige verwendet
      blankIds,
    });
  };

  // Generiere die Vorschau mit Lücken
  const renderPreview = () => {
    return parsed.textParts.map((part, i) => (
      <span key={i}>
        {part}
        {i < parsed.correctWords.length && (
          <span className={`inline-flex items-center justify-center min-w-[80px] mx-1 px-2 py-0.5 rounded border-2 ${
            showSolution
              ? 'bg-blue-50 border-blue-300 text-blue-700 font-medium'
              : 'bg-slate-100 border-dashed border-slate-300 text-slate-400'
          }`}>
            {showSolution ? parsed.correctWords[i] : '______'}
          </span>
        )}
      </span>
    ));
  };

  return (
    <Card className={isDeleted ? 'border-red-300 bg-red-50/50 opacity-70' : 'border-slate-200'}>
      <CardHeader className={isDeleted ? 'bg-red-100/50 border-b border-red-200' : 'bg-slate-50 border-b border-slate-200'}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <GripVertical className="w-5 h-5 text-slate-400 cursor-move" />
            <CardTitle className={isDeleted ? 'text-red-700' : 'text-slate-900'}>
              Frage {index + 1}: Lueckentext
            </CardTitle>
            {isDeleted && (
              <Badge className="bg-red-100 text-red-700 border-red-300">
                Wird geloescht
              </Badge>
            )}
          </div>
          {isDeleted ? (
            <Button
              onClick={onUndoDelete}
              variant="ghost"
              size="sm"
              className="text-green-600 hover:text-green-700 hover:bg-green-50"
            >
              <Undo2 className="w-4 h-4 mr-1" />
              Rueckgaengig
            </Button>
          ) : (
            <Button
              onClick={onDelete}
              variant="ghost"
              size="sm"
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-6 space-y-4">
        {/* Hilfetext */}
        <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-blue-800">
            Markiere Loesungswoerter mit <code className="px-1.5 py-0.5 bg-blue-100 rounded text-blue-900 font-mono">{'{{doppelten Klammern}}'}</code>
          </p>
        </div>

        {/* Raw-Text Editor */}
        <div>
          <Label htmlFor={`cloze-text-${index}`}>Text mit Luecken</Label>
          <Textarea
            id={`cloze-text-${index}`}
            value={rawText}
            onChange={(e) => handleTextChange(e.target.value)}
            rows={4}
            className="mt-2 font-mono"
            placeholder="Bei {{Beispiel}} handelt es sich um einen Lueckentext. Das Wort {{Beispiel}} wird zur Luecke."
          />
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-2">
          {hasValidGaps ? (
            <Badge className="bg-green-50 text-green-700 border border-green-200">
              <Check className="w-3 h-3 mr-1" />
              {gapCount} {gapCount === 1 ? 'Luecke' : 'Luecken'} erkannt
            </Badge>
          ) : (
            <Badge className="bg-yellow-50 text-yellow-700 border border-yellow-200">
              <AlertCircle className="w-3 h-3 mr-1" />
              Keine Luecken definiert
            </Badge>
          )}
        </div>

        {/* Vorschau */}
        {hasValidGaps && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>Vorschau</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSolution(!showSolution)}
                className="text-slate-600 hover:text-slate-900 h-7 px-2"
              >
                {showSolution ? (
                  <>
                    <EyeOff className="w-3.5 h-3.5 mr-1" />
                    Loesungen verbergen
                  </>
                ) : (
                  <>
                    <Eye className="w-3.5 h-3.5 mr-1" />
                    Loesungen anzeigen
                  </>
                )}
              </Button>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 leading-relaxed">
              {renderPreview()}
            </div>

            {/* Lösungsliste */}
            <div className="mt-3 flex items-center gap-2 text-sm text-slate-600">
              <span className="font-medium">Loesungen:</span>
              {parsed.correctWords.map((word, i) => (
                <span key={i} className="px-2 py-0.5 bg-slate-100 rounded">
                  {i + 1}. {word}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export interface PendingChanges {
  questions: Question[];
  deletedIds: string[];
  updatedQuestions: Question[];
}

interface QuizEditViewProps {
  quizId: string;
  quizTitle: string;
  quizTheme: string;
  questions: Question[];
  onSave: (changes: PendingChanges) => Promise<void>;
  onBack: () => void;
}

export function QuizEditView({
  quizId,
  quizTitle,
  quizTheme,
  questions: initialQuestions,
  onSave,
  onBack,
}: QuizEditViewProps) {
  const [questions, setQuestions] = useState<Question[]>(initialQuestions);
  const [originalQuestions] = useState<Question[]>(initialQuestions);
  const [pendingDeletions, setPendingDeletions] = useState<Set<string>>(new Set());
  const [isSaving, setIsSaving] = useState(false);

  // Berechne geänderte Questions (ohne gelöschte)
  const modifiedQuestions = useMemo(() => {
    return questions.filter((q) => {
      if (pendingDeletions.has(q.id)) return false;
      const original = originalQuestions.find((oq) => oq.id === q.id);
      if (!original) return false;
      return JSON.stringify(q) !== JSON.stringify(original);
    });
  }, [questions, originalQuestions, pendingDeletions]);

  // Prüfe ob es Änderungen gibt
  const hasChanges = modifiedQuestions.length > 0 || pendingDeletions.size > 0;

  const updateQuestion = (index: number, updatedQuestion: Question) => {
    const newQuestions = [...questions];
    newQuestions[index] = updatedQuestion;
    setQuestions(newQuestions);
  };

  const deleteQuestion = (index: number) => {
    const question = questions[index];
    if (!question) {
      return;
    }
    // Markiere als pending deletion (kein sofortiger API-Call)
    setPendingDeletions((prev) => new Set(prev).add(question.id));
  };

  const undoDeletion = (questionId: string) => {
    setPendingDeletions((prev) => {
      const newSet = new Set(prev);
      newSet.delete(questionId);
      return newSet;
    });
  };

  const undoAllDeletions = () => {
    setPendingDeletions(new Set());
  };

  const handleSave = async () => {
    if (!hasChanges) return;

    setIsSaving(true);
    try {
      const remainingQuestions = questions.filter((q) => !pendingDeletions.has(q.id));

      await onSave({
        questions: remainingQuestions,
        deletedIds: Array.from(pendingDeletions),
        updatedQuestions: modifiedQuestions,
      });

      // Reset state nach erfolgreichem Speichern
      setPendingDeletions(new Set());
    } finally {
      setIsSaving(false);
    }
  };

  const renderQuestionEditor = (question: Question, index: number) => {
    const isDeleted = pendingDeletions.has(question.id);

    if (question.type === 'multiple-choice') {
      return (
        <Card
          key={question.id}
          className={
            isDeleted
              ? 'border-red-300 bg-red-50/50 opacity-70'
              : 'border-slate-200'
          }
        >
          <CardHeader
            className={
              isDeleted
                ? 'bg-red-100/50 border-b border-red-200'
                : 'bg-slate-50 border-b border-slate-200'
            }
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <GripVertical className="w-5 h-5 text-slate-400 cursor-move" />
                <CardTitle className={isDeleted ? 'text-red-700' : 'text-slate-900'}>
                  Frage {index + 1}: Multiple Choice
                </CardTitle>
                {isDeleted && (
                  <Badge className="bg-red-100 text-red-700 border-red-300">
                    Wird geloescht
                  </Badge>
                )}
              </div>
              {isDeleted ? (
                <Button
                  onClick={() => undoDeletion(question.id)}
                  variant="ghost"
                  size="sm"
                  className="text-green-600 hover:text-green-700 hover:bg-green-50"
                >
                  <Undo2 className="w-4 h-4 mr-1" />
                  Rueckgaengig
                </Button>
              ) : (
                <Button
                  onClick={() => deleteQuestion(index)}
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div>
              <Label htmlFor={`question-${index}`}>Fragestellung</Label>
              <Textarea
                id={`question-${index}`}
                value={question.question}
                onChange={(e) =>
                  updateQuestion(index, { ...question, question: e.target.value })
                }
                rows={2}
                className="mt-1"
              />
            </div>

            <div>
              <Label>Antwortoptionen (Wählen Sie die richtige(n) Antwort(en))</Label>
              <div className="mt-2 space-y-2">
                {question.options.map((option, optionIndex) => (
                  <div key={optionIndex} className="flex items-start gap-3 p-3 border border-slate-200 rounded-lg">
                    <Checkbox
                      checked={question.correctAnswers.includes(optionIndex)}
                      onCheckedChange={(checked) => {
                        const newCorrectAnswers = checked
                          ? [...question.correctAnswers, optionIndex]
                          : question.correctAnswers.filter((i) => i !== optionIndex);
                        updateQuestion(index, {
                          ...question,
                          correctAnswers: newCorrectAnswers,
                        });
                      }}
                      className="mt-1"
                    />
                    <Input
                      value={option}
                      onChange={(e) => {
                        const newOptions = [...question.options];
                        newOptions[optionIndex] = e.target.value;
                        updateQuestion(index, { ...question, options: newOptions });
                      }}
                      className="flex-1"
                      placeholder={`Option ${optionIndex + 1}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    if (question.type === 'freitext') {
      return (
        <Card
          key={question.id}
          className={
            isDeleted
              ? 'border-red-300 bg-red-50/50 opacity-70'
              : 'border-slate-200'
          }
        >
          <CardHeader
            className={
              isDeleted
                ? 'bg-red-100/50 border-b border-red-200'
                : 'bg-slate-50 border-b border-slate-200'
            }
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <GripVertical className="w-5 h-5 text-slate-400 cursor-move" />
                <CardTitle className={isDeleted ? 'text-red-700' : 'text-slate-900'}>
                  Frage {index + 1}: Freitext
                </CardTitle>
                {isDeleted && (
                  <Badge className="bg-red-100 text-red-700 border-red-300">
                    Wird geloescht
                  </Badge>
                )}
              </div>
              {isDeleted ? (
                <Button
                  onClick={() => undoDeletion(question.id)}
                  variant="ghost"
                  size="sm"
                  className="text-green-600 hover:text-green-700 hover:bg-green-50"
                >
                  <Undo2 className="w-4 h-4 mr-1" />
                  Rueckgaengig
                </Button>
              ) : (
                <Button
                  onClick={() => deleteQuestion(index)}
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div>
              <Label htmlFor={`question-${index}`}>Fragestellung</Label>
              <Textarea
                id={`question-${index}`}
                value={question.question}
                onChange={(e) =>
                  updateQuestion(index, { ...question, question: e.target.value })
                }
                rows={2}
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor={`solution-${index}`}>Musterlösung</Label>
              <Textarea
                id={`solution-${index}`}
                value={question.solution}
                onChange={(e) =>
                  updateQuestion(index, { ...question, solution: e.target.value })
                }
                rows={4}
                className="mt-1"
              />
            </div>
          </CardContent>
        </Card>
      );
    }

    if (question.type === 'lueckentext') {
      return (
        <ClozeEditor
          key={question.id}
          question={question}
          index={index}
          isDeleted={isDeleted}
          onUpdate={(updated) => updateQuestion(index, updated)}
          onDelete={() => deleteQuestion(index)}
          onUndoDelete={() => undoDeletion(question.id)}
        />
      );
    }

    return null;
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <Button
          onClick={onBack}
          variant="ghost"
          className="mb-4 -ml-2 text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Zurück
        </Button>

        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-slate-900 text-[28px] mb-2">Quiz bearbeiten</h2>
            <p className="text-slate-600">
              {quizTitle} - {quizTheme}
            </p>
          </div>

          <Button
            onClick={() => void handleSave()}
            disabled={!hasChanges || isSaving}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300"
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Speichern...' : 'Aenderungen speichern'}
          </Button>
        </div>

        {hasChanges && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 flex-wrap">
                <p className="text-sm text-yellow-800">
                  Ungespeicherte Aenderungen
                </p>
                {pendingDeletions.size > 0 && (
                  <Badge className="bg-red-50 text-red-700 border border-red-200">
                    {pendingDeletions.size} Loeschung{pendingDeletions.size > 1 ? 'en' : ''}
                  </Badge>
                )}
                {modifiedQuestions.length > 0 && (
                  <Badge className="bg-blue-50 text-blue-700 border border-blue-200">
                    {modifiedQuestions.length} Bearbeitung{modifiedQuestions.length > 1 ? 'en' : ''}
                  </Badge>
                )}
              </div>
              {pendingDeletions.size > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={undoAllDeletions}
                  className="text-yellow-800 hover:text-yellow-900 hover:bg-yellow-100"
                >
                  <Undo2 className="w-4 h-4 mr-1" />
                  Alle Loeschungen rueckgaengig
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {questions.map((question, index) => renderQuestionEditor(question, index))}
      </div>

      {questions.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <p className="text-slate-500">
            Keine Fragen vorhanden. Fügen Sie neue Fragen hinzu, um das Quiz zu bearbeiten.
          </p>
        </div>
      )}
    </div>
  );
}
