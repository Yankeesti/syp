import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '../../../shared/ui/button';
import { Badge } from '../../../shared/ui/badge';
import { Input } from '../../../shared/ui/input';
import { Label } from '../../../shared/ui/label';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../../../shared/ui/alert-dialog';
import type { ShareLinkApi } from '../model/types';

type ShareLinkStatus = 'idle' | 'loading' | 'loaded' | 'error';

type ShareLinkCreatePayload = {
  durationSeconds: number | null;
  maxUses: number | null;
};

type ShareLinksViewProps = {
  quizTitle: string;
  quizTheme?: string;
  links: ShareLinkApi[];
  status: ShareLinkStatus;
  error: string | null;
  isCreating: boolean;
  revokingId: string | null;
  onCreate: (payload: ShareLinkCreatePayload) => Promise<boolean>;
  onRevoke: (shareLinkId: string) => Promise<void>;
  onRefresh: () => Promise<void>;
  onBack: () => void;
};

const durationOptions = [
  { label: '1 Stunde', value: '3600' },
  { label: '24 Stunden', value: '86400' },
  { label: '7 Tage', value: '604800' },
  { label: '30 Tage', value: '2592000' },
  { label: 'Benutzerdefiniert', value: 'custom' },
  { label: 'Niemals', value: 'never' },
];

const durationUnits = [
  { label: 'Minuten', value: '60' },
  { label: 'Stunden', value: '3600' },
  { label: 'Tage', value: '86400' },
];

const formatDateTime = (date: Date) => {
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

export function ShareLinksView({
  quizTitle,
  quizTheme,
  links,
  status,
  error,
  isCreating,
  revokingId,
  onCreate,
  onRevoke,
  onRefresh,
  onBack,
}: ShareLinksViewProps) {
  const [activeTab, setActiveTab] = useState<'create' | 'links'>('create');
  const [durationChoice, setDurationChoice] = useState<string>('86400');
  const [customDurationValue, setCustomDurationValue] = useState('');
  const [customDurationUnit, setCustomDurationUnit] = useState('3600');
  const [maxUsesInput, setMaxUsesInput] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const sortedLinks = useMemo(
    () =>
      [...links].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [links],
  );

  useEffect(() => {
    void onRefresh();
  }, [onRefresh]);

  const handleCreate = async () => {
    let durationSeconds: number | null = null;
    if (durationChoice === 'never') {
      durationSeconds = null;
    } else if (durationChoice === 'custom') {
      const trimmedDuration = customDurationValue.trim();
      if (!trimmedDuration) {
        setFormError('Bitte eine Gueltigkeitsdauer angeben.');
        return;
      }
      const parsedValue = Number(trimmedDuration);
      const unitSeconds = Number(customDurationUnit);
      const computedSeconds = parsedValue * unitSeconds;
      if (!Number.isFinite(computedSeconds) || computedSeconds <= 0) {
        setFormError('Gueltigkeitsdauer muss eine positive Zahl sein.');
        return;
      }
      durationSeconds = computedSeconds;
    } else {
      const parsedPreset = Number(durationChoice);
      if (!Number.isFinite(parsedPreset) || parsedPreset <= 0) {
        setFormError('Gueltigkeitsdauer muss eine positive Zahl sein.');
        return;
      }
      durationSeconds = parsedPreset;
    }

    const trimmedMaxUses = maxUsesInput.trim();
    if (trimmedMaxUses) {
      const parsed = Number(trimmedMaxUses);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        setFormError('Max. Nutzungen muss eine positive Zahl sein.');
        return;
      }
    }

    setFormError(null);
    const maxUsesValue = trimmedMaxUses ? Number(trimmedMaxUses) : null;
    const success = await onCreate({
      durationSeconds,
      maxUses: maxUsesValue,
    });
    if (success) {
      setActiveTab('links');
      setMaxUsesInput('');
      setCustomDurationValue('');
    }
  };

  const handleCopy = async (link: ShareLinkApi) => {
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(link.url);
        setCopiedId(link.share_link_id);
        window.setTimeout(() => setCopiedId(null), 1600);
        return;
      }
    } catch {
      // Fallback below.
    }
    window.prompt('Link kopieren:', link.url);
  };

  const shortenUrl = (url: string) => {
    if (url.length <= 48) {
      return url;
    }
    return `${url.slice(0, 32)}...${url.slice(-10)}`;
  };

  const getShareStatus = (link: ShareLinkApi) => {
    const expiresAt = link.expires_at ? new Date(link.expires_at) : null;
    const isExpired = expiresAt ? expiresAt.getTime() < Date.now() : false;
    const isUsedUp =
      link.max_uses !== null && link.current_uses >= link.max_uses;

    if (!link.is_active) {
      return {
        label: 'Widerrufen',
        className: 'bg-slate-100 text-slate-600 border-slate-200',
      };
    }
    if (isExpired) {
      return {
        label: 'Abgelaufen',
        className: 'bg-red-50 text-red-700 border-red-200',
      };
    }
    if (isUsedUp) {
      return {
        label: 'Aufgebraucht',
        className: 'bg-yellow-50 text-yellow-700 border-yellow-200',
      };
    }
    return {
      label: 'Aktiv',
      className: 'bg-green-50 text-green-700 border-green-200',
    };
  };

  const renderCreateForm = () => (
    <div className="space-y-4">
      <div>
        <Label className="text-sm text-slate-600">Gueltigkeitsdauer</Label>
        <select
          value={durationChoice}
          onChange={(event) => {
            setDurationChoice(event.target.value);
            setFormError(null);
          }}
          className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {durationOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {durationChoice === 'custom' && (
          <div className="mt-2 flex gap-2">
            <Input
              type="number"
              min="1"
              step="1"
              value={customDurationValue}
              onChange={(event) => {
                setCustomDurationValue(event.target.value);
                setFormError(null);
              }}
              placeholder="z.B. 12"
            />
            <select
              value={customDurationUnit}
              onChange={(event) => {
                setCustomDurationUnit(event.target.value);
                setFormError(null);
              }}
              className="w-40 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {durationUnits.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        )}
        <p className="text-xs text-slate-500 mt-1">Optional, Standard: 24 Stunden</p>
      </div>
      <div>
        <Label className="text-sm text-slate-600">Max. Nutzungen</Label>
        <Input
          type="number"
          min="1"
          step="1"
          value={maxUsesInput}
          onChange={(event) => setMaxUsesInput(event.target.value)}
          placeholder="z.B. 10"
        />
        <p className="text-xs text-slate-500 mt-1">Leer = unbegrenzt</p>
      </div>
      {formError && <p className="text-sm text-red-600">{formError}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex justify-end">
        <Button onClick={handleCreate} disabled={isCreating}>
          {isCreating ? 'Erstelle...' : 'Link erstellen'}
        </Button>
      </div>
    </div>
  );

  const renderLinks = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-600">
          Alle vorhandenen Links fuer dieses Quiz.
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void onRefresh()}
          disabled={status === 'loading'}
          className="border-slate-300"
        >
          Aktualisieren
        </Button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {status === 'loading' && sortedLinks.length === 0 && (
        <p className="text-sm text-slate-500">Links werden geladen...</p>
      )}
      {status !== 'loading' && sortedLinks.length === 0 && (
        <p className="text-sm text-slate-500">Noch keine Links vorhanden.</p>
      )}
      {sortedLinks.length > 0 && (
        <div className="space-y-3">
          {sortedLinks.map((link) => {
            const statusInfo = getShareStatus(link);
            const usageLabel =
              link.max_uses !== null
                ? `${link.current_uses} / ${link.max_uses}`
                : `${link.current_uses} / unbegrenzt`;
            const expiresLabel = link.expires_at
              ? formatDateTime(new Date(link.expires_at))
              : 'Nie';

            return (
              <div
                key={link.share_link_id}
                className="rounded-lg border border-slate-200 p-4 space-y-3"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <p
                      className="text-sm font-medium text-slate-900"
                      title={link.url}
                    >
                      {shortenUrl(link.url)}
                    </p>
                    <p className="text-xs text-slate-500">
                      Erstellt: {formatDateTime(new Date(link.created_at))}
                    </p>
                  </div>
                  <Badge className={statusInfo.className}>{statusInfo.label}</Badge>
                </div>
                <div className="grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                  <div>Ablauf: {expiresLabel}</div>
                  <div>Nutzung: {usageLabel}</div>
                  <div>Status: {statusInfo.label}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void handleCopy(link)}
                    className="border-slate-300"
                  >
                    {copiedId === link.share_link_id ? 'Kopiert' : 'Link kopieren'}
                  </Button>
                  {link.is_active && (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700"
                        >
                          Widerrufen
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Link wirklich widerrufen?</AlertDialogTitle>
                          <AlertDialogDescription>
                            Danach kann der Link nicht mehr genutzt werden.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Abbrechen</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => void onRevoke(link.share_link_id)}
                            className="bg-red-600 hover:bg-red-700 text-white"
                            disabled={revokingId === link.share_link_id}
                          >
                            {revokingId === link.share_link_id ? 'Widerrufe...' : 'Widerrufen'}
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <Button
          onClick={onBack}
          variant="ghost"
          className="mb-4 -ml-2 text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Zurueck zum Quiz
        </Button>

        <div className="mb-6">
          <h2 className="text-slate-900 text-[24px] mb-2">Quiz teilen</h2>
          <p className="text-slate-600">
            Erstelle und verwalte Freigabe-Links fuer dieses Quiz.
          </p>
          <p className="text-sm text-slate-500 mt-2">
            Quiz: {quizTitle}
            {quizTheme ? ` - ${quizTheme}` : ''}
          </p>
        </div>

        <div className="flex gap-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab('create')}
            className={`px-3 py-2 text-sm rounded-md ${
              activeTab === 'create'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Neuer Link
          </button>
          <button
            onClick={() => setActiveTab('links')}
            className={`px-3 py-2 text-sm rounded-md ${
              activeTab === 'links'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Meine Links
          </button>
        </div>

        <div className="mt-4">
          {activeTab === 'create' ? renderCreateForm() : renderLinks()}
        </div>
      </div>
    </div>
  );
}
