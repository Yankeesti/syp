import { useState } from 'react';
import { AlertTriangle, Trash2, LogOut, User, LayoutList, Home, Send } from 'lucide-react';
import { routes } from '../routes';
import { deleteAccount, reportError } from '../../features/auth/model/authApi';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../../shared/ui/dropdown-menu';
import { isApiError } from '../../shared/api/client';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../../shared/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../shared/ui/dialog';
import { Button } from '../../shared/ui/button';

interface NavigationSidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  userEmail: string;
  onLogout?: () => void;
}

export function NavigationSidebar({ currentPath, onNavigate, userEmail, onLogout }: NavigationSidebarProps) {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [deleteAccountError, setDeleteAccountError] = useState('');
  const [isReportErrorDialogOpen, setIsReportErrorDialogOpen] = useState(false);
  const [errorReport, setErrorReport] = useState('');
  const [isSendingErrorReport, setIsSendingErrorReport] = useState(false);
  const [errorReportError, setErrorReportError] = useState('');
  const [errorReportSuccess, setErrorReportSuccess] = useState('');

  const handleReportError = () => {
    setErrorReportError('');
    setErrorReportSuccess('');
    setIsReportErrorDialogOpen(true);
  };

  const handleSubmitErrorReport = async () => {
    if (!errorReport.trim() || isSendingErrorReport) {
      return;
    }

    setIsSendingErrorReport(true);
    setErrorReportError('');
    setErrorReportSuccess('');

    try {
      await reportError(errorReport.trim(), userEmail);
      setIsSendingErrorReport(false);
      setErrorReport('');
      setErrorReportSuccess('Fehlerbericht gesendet.');
    } catch (error) {
      let message = 'Fehlerbericht konnte nicht gesendet werden.';
      if (isApiError(error)) {
        if (error.status === 401 || error.status === 403) {
          message = 'Nicht autorisiert. Bitte melde dich erneut an.';
        } else {
          message = error.message;
        }
      } else if (error instanceof Error) {
        message = error.message;
      }
      setErrorReportError(message);
      setIsSendingErrorReport(false);
    }
  };

  const handleDeleteAccount = () => {
    setDeleteAccountError('');
    setIsDeletingAccount(false);
    setIsDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (isDeletingAccount) {
      return;
    }

    setIsDeletingAccount(true);
    setDeleteAccountError('');

    try {
      await deleteAccount();
      setIsDeletingAccount(false);
      setIsDeleteDialogOpen(false);
      if (onLogout) {
        onLogout();
      } else {
        alert('Account wurde geloescht.');
      }
    } catch (error) {
      let message = 'Account konnte nicht geloescht werden.';
      if (isApiError(error)) {
        if (error.status === 401 || error.status === 403) {
          message = 'Nicht autorisiert. Bitte melde dich erneut an.';
        } else if (error.status === 404) {
          message = 'Account wurde nicht gefunden.';
        } else {
          message = error.message;
        }
      } else if (error instanceof Error) {
        message = error.message;
      }
      setDeleteAccountError(message);
      setIsDeletingAccount(false);
    }
  };

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    } else {
      alert('Abmelden - Funktion wird implementiert');
    }
  };

  const navItems = [
    {
      id: 'home' as const,
      label: 'Startseite',
      icon: Home,
      path: routes.quiz.root,
      exact: true,
    },
    {
      id: 'quiz-list' as const,
      label: 'Quizze',
      icon: LayoutList,
      path: routes.quiz.list,
      exact: false,
    },
  ];

  return (
    <>
      <aside className="w-64 bg-white border-r border-slate-200 p-6 min-h-[calc(100vh-73px)] flex flex-col">
        <nav className="space-y-2 flex-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.exact
              ? currentPath === item.path
              : currentPath.startsWith(item.path);

            return (
              <Button
                key={item.id}
                onClick={() => onNavigate(item.path)}
                variant="ghost"
                className={`w-full justify-start ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                {item.label}
              </Button>
            );
          })}
        </nav>

        <div className="mt-6 pt-6 border-t border-slate-200">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-3 w-full hover:bg-slate-50 p-2 rounded-lg transition-colors">
                <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center text-white">
                  <User className="w-6 h-6" />
                </div>
                <div className="text-left">
                  <div className="text-sm text-slate-900">{userEmail}</div>
                </div>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              <DropdownMenuItem onClick={handleReportError} className="cursor-pointer">
                <AlertTriangle className="w-4 h-4 mr-2" />
                Fehler melden
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleDeleteAccount} className="cursor-pointer text-red-600">
                <Trash2 className="w-4 h-4 mr-2" />
                Account löschen
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="cursor-pointer">
                <LogOut className="w-4 h-4 mr-2" />
                Abmelden
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      <Dialog open={isReportErrorDialogOpen} onOpenChange={setIsReportErrorDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
              <DialogTitle className="text-slate-900">Fehler melden</DialogTitle>
            </div>
            <DialogDescription className="text-slate-600 pt-2">
              Beschreiben Sie bitte den aufgetretenen Fehler oder das Problem, damit wir es beheben können.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <textarea
              value={errorReport}
              onChange={(e) => setErrorReport(e.target.value)}
              placeholder="Bitte beschreiben Sie hier den Fehler..."
              className="w-full h-32 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
            {errorReportError && (
              <p className="mt-2 text-sm text-red-600">{errorReportError}</p>
            )}
            {errorReportSuccess && !errorReportError && (
              <p className="mt-2 text-sm text-green-600">{errorReportSuccess}</p>
            )}
          </div>
          <DialogFooter>
            <Button
              onClick={() => {
                setErrorReport('');
                setIsReportErrorDialogOpen(false);
              }}
              variant="outline"
              className="bg-white border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              Abbrechen
            </Button>
            <Button
              onClick={() => {
                void handleSubmitErrorReport();
              }}
              disabled={!errorReport.trim() || isSendingErrorReport}
              className="bg-blue-600 hover:bg-blue-700 text-white disabled:bg-slate-300 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4 mr-2" />
              {isSendingErrorReport ? 'Senden...' : 'Absenden'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={(open) => {
          if (isDeletingAccount) {
            return;
          }
          if (!open) {
            setDeleteAccountError('');
          }
          setIsDeleteDialogOpen(open);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <AlertDialogTitle className="text-slate-900">Account löschen</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="text-slate-600 pt-2">
              Möchten Sie Ihren Account wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.
            </AlertDialogDescription>
            {deleteAccountError && (
              <div className="text-sm text-red-600">{deleteAccountError}</div>
            )}
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              className="bg-white border-slate-300 text-slate-700 hover:bg-slate-50"
              disabled={isDeletingAccount}
            >
              Abbrechen
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(event) => {
                event.preventDefault();
                void handleConfirmDelete();
              }}
              className="bg-red-600 hover:bg-red-700 text-white"
              disabled={isDeletingAccount}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {isDeletingAccount ? 'Loesche...' : 'Endgueltig loeschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
