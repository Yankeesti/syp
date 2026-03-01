import { useState, useRef } from 'react';
import { Sparkles, CheckSquare, FileText, Type, Upload, X, ArrowLeft } from 'lucide-react';
import type { QuestionType } from '../entities/question/types';
import { Button } from '../../../shared/ui/button';
import { Checkbox } from '../../../shared/ui/checkbox';

interface QuizGenerateViewProps {
  onGenerate: (prompt: string, types: QuestionType[], pdfFile?: File) => void;
  onBack: () => void;
}

export function QuizGenerateView({ onGenerate, onBack }: QuizGenerateViewProps) {
  const [inputText, setInputText] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<QuestionType[]>(['multiple-choice']);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const questionTypes = [
    { id: 'multiple-choice' as QuestionType, label: 'Multiple Choice', icon: CheckSquare },
    { id: 'freitext' as QuestionType, label: 'Freitext', icon: FileText },
    { id: 'lueckentext' as QuestionType, label: 'Lückentext', icon: Type },
  ];

  const toggleType = (type: QuestionType) => {
    if (selectedTypes.includes(type)) {
      // Don't allow deselecting if it's the last selected type
      if (selectedTypes.length > 1) {
        setSelectedTypes(selectedTypes.filter(t => t !== type));
      }
    } else {
      setSelectedTypes([...selectedTypes, type]);
    }
  };

  const handleGenerate = () => {
    if (!inputText.trim() && !uploadedFile) return;
    if (selectedTypes.length === 0) return;
    
    // Combine instructions: PDF filename + user prompt
    let prompt = '';
    if (uploadedFile && inputText.trim()) {
      prompt = `${inputText}`;
    } else if (uploadedFile) {
      prompt = `Erstelle Fragen basierend auf der PDF: ${uploadedFile.name}`;
    } else {
      prompt = inputText;
    }
    
    onGenerate(prompt, selectedTypes, uploadedFile || undefined);
    setInputText('');
    setUploadedFile(null);
    setSelectedTypes(['multiple-choice']);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setUploadedFile(file);
    }
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleBrowseFiles = () => {
    fileInputRef.current?.click();
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
          Zurück zur Übersicht
        </Button>

        <h2 className="text-slate-900 text-[24px] mb-2">Neues Quiz generieren</h2>
        <p className="text-slate-600 mb-6">
          Laden Sie eine PDF-Datei hoch oder geben Sie ein Thema ein, zu dem Fragen generiert werden sollen
        </p>

        <div className="space-y-6">
          <div>
            <label className="block text-sm text-slate-600 mb-2">
              Aufgabentypen wählen (Mehrfachauswahl möglich):
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {questionTypes.map(({ id, label, icon: Icon }) => {
                const isSelected = selectedTypes.includes(id);
                return (
                  <div
                    key={id}
                    onClick={() => toggleType(id)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-blue-50 border-blue-500 text-blue-700'
                        : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleType(id)}
                      className="pointer-events-none"
                    />
                    <Icon className="w-4 h-4" />
                    <span className="text-sm flex-1 text-left">{label}</span>
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Mindestens ein Typ muss ausgewählt sein. Die Fragen werden gleichmäßig auf die ausgewählten Typen verteilt.
            </p>
          </div>
          
          <div>
            <label className="block text-sm text-slate-600 mb-2">PDF-Datei hochladen (optional):</label>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              className="hidden"
            />
            
            {uploadedFile ? (
              <div className="flex items-center gap-3 px-4 py-3 bg-green-50 border-2 border-green-500 rounded-lg">
                <FileText className="w-5 h-5 text-green-600" />
                <span className="flex-1 text-sm text-green-800">{uploadedFile.name}</span>
                <button
                  onClick={handleRemoveFile}
                  className="p-1 hover:bg-green-100 rounded transition-colors"
                >
                  <X className="w-4 h-4 text-green-600" />
                </button>
              </div>
            ) : (
              <button
                onClick={handleBrowseFiles}
                className="w-full px-4 py-3 border-2 border-dashed border-slate-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all flex items-center justify-center gap-2 text-slate-600"
              >
                <Upload className="w-5 h-5" />
                <span className="text-sm">PDF-Datei auswählen</span>
              </button>
            )}
          </div>
          
          <div>
            <label className="block text-sm text-slate-600 mb-2">
              Anweisungen für die Fragengenerierung {uploadedFile && '(Anzahl & Fokus)'}:
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={uploadedFile 
                ? "z.B. Erstelle 20 Fragen. Fokussiere auf die Kapitel 3-5 und die wichtigsten Definitionen..."
                : "z.B. Erstelle 15 Fragen zu React Hooks. Fokussiere auf useState, useEffect und Custom Hooks..."}
              rows={4}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          <div className="flex justify-end">
            <Button
              onClick={handleGenerate}
              disabled={(!inputText.trim() && !uploadedFile) || selectedTypes.length === 0}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Quiz generieren
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
