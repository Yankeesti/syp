import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { registerUser } from '../model/authApi';
import { setUserEmail } from '../model/tokenStorage';

interface RegisterScreenProps {
  onBack: () => void;
  onPrivacyPolicy: () => void;
}

export function RegisterScreen({ onBack, onPrivacyPolicy }: RegisterScreenProps) {
  const [email, setEmail] = useState('');
  const [acceptedPrivacy, setAcceptedPrivacy] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!acceptedPrivacy) {
      setErrorMessage('Bitte akzeptieren Sie die Datenschutzerklaerung.');
      return;
    }
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const response = await registerUser(email);
      setUserEmail(email);
      setSuccessMessage(
        response.message ||
          'Registrierung erfolgreich. Wir haben dir einen Login-Link gesendet. Bitte pruefe dein Postfach.',
      );
    } catch (error) {
      const fallback = 'Senden des Magic-Links fehlgeschlagen.';
      setErrorMessage(error instanceof Error ? error.message : fallback);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="dark-header py-2 px-6">
        <h1 className="text-center text-lg">KI Tutor</h1>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col px-4 py-2">
        <button
          onClick={onBack}
          className="ki-link flex items-center gap-1 mb-2 self-start text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Zurück</span>
        </button>

        <div className="flex-1 flex items-center justify-center">
          <div className="w-96">
            <div className="ki-card p-4">
              <div className="text-center mb-3">
                <h2 className="ki-title mb-2 text-lg">Registrieren</h2>
              </div>

              <form onSubmit={handleSubmit} className="space-y-2">
                <div>
                  <label className="ki-title block mb-1 text-sm">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="ki-input w-full py-2 px-3 text-sm"
                    placeholder="ihre-email@beispiel.de"
                    required
                  />
                </div>

                {errorMessage && (
                  <div className="text-sm text-red-600">{errorMessage}</div>
                )}
                {successMessage && (
                  <div className="text-sm text-green-600">{successMessage}</div>
                )}

                <div className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    id="privacy-checkbox"
                    checked={acceptedPrivacy}
                    onChange={(e) => setAcceptedPrivacy(e.target.checked)}
                    className="mt-0.5 w-3.5 h-3.5 rounded border-gray-300 accent-[#7B9CB5] cursor-pointer"
                    required
                  />
                  <label htmlFor="privacy-checkbox" className="text-gray-700 cursor-pointer text-xs leading-tight">
                    Ich habe die{' '}
                    <button
                      type="button"
                      onClick={onPrivacyPolicy}
                      className="ki-link inline"
                    >
                      Datenschutzerklärung
                    </button>{' '}
                    gelesen und akzeptiere sie.
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="ki-button-primary w-full py-2 text-sm mt-2"
                >
                  {isSubmitting ? 'Sende...' : 'Link senden'}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

