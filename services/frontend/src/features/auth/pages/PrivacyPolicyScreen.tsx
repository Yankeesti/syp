import { ArrowLeft } from 'lucide-react';

interface PrivacyPolicyScreenProps {
  onBack: () => void;
}

export function PrivacyPolicyScreen({ onBack }: PrivacyPolicyScreenProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="dark-header py-4 px-6">
        <h1 className="text-center">KI Tutor</h1>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col px-4 py-8">
        <button
          onClick={onBack}
          className="ki-link flex items-center gap-2 mb-8 self-start"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Zurück</span>
        </button>

        <div className="flex-1 flex items-start justify-center">
          <div className="w-full max-w-3xl">
            <div className="ki-card p-8">
              <h2 className="ki-title mb-6">Datenschutzerklärung</h2>
              
              <div className="space-y-6 text-gray-700">
                <section>
                  <h3 className="ki-title mb-3">1. Allgemeine Hinweise</h3>
                  <div className="space-y-3">
                    <p>
                      Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen.
                    </p>
                    <p>
                      Personenbezogene Daten sind alle Daten, mit denen Sie persönlich identifiziert werden können.
                    </p>
                  </div>
                </section>

                <section>
                  <h3 className="ki-title mb-3">2. Datenerfassung auf dieser Website</h3>
                  <div className="space-y-3">
                    <h4 className="ki-title">Wer ist verantwortlich für die Datenerfassung?</h4>
                    <p>
                      Die Datenverarbeitung auf dieser Website erfolgt durch den Betreiber dieser Website.
                    </p>
                    
                    <h4 className="ki-title mt-4">Wie erfassen wir Ihre Daten?</h4>
                    <p>
                      Ihre Daten werden erhoben, wenn Sie uns diese mitteilen.
                    </p>
                    <p>
                      Das können zum Beispiel Daten sein, die Sie in ein Kontaktformular eingeben oder bei der Registrierung angeben.
                    </p>
                    <p>
                      Außerdem werden beim Besuch der Website automatisch technische Daten durch unsere IT Systeme erfasst.
                    </p>
                    <p>
                      Das sind vor allem technische Daten wie Browsertyp, verwendetes Betriebssystem oder Zeitpunkt des Seitenaufrufs.
                    </p>
                    <p>
                      Diese Daten werden automatisch erhoben, sobald Sie diese Website nutzen.
                    </p>
                  </div>
                </section>

                <section>
                  <h3 className="ki-title mb-3">3. Registrierung und Login</h3>
                  <div className="space-y-3">
                    <p>
                      Sie können sich auf dieser Website registrieren, um zusätzliche Funktionen zu nutzen.
                    </p>
                    <p>
                      Die dabei eingegebenen Daten verwenden wir nur zum Zweck der Nutzung des jeweiligen Angebotes oder Dienstes, für den Sie sich registriert haben.
                    </p>
                    <p>
                      Bei der Registrierung werden folgende Daten erhoben:
                    </p>
                    <ul className="list-disc pl-6 space-y-1">
                      <li>E Mail Adresse</li>
                      <li>IP Adresse und Zeitpunkt der Registrierung</li>
                    </ul>
                    <p>
                      Die Daten werden verschlüsselt übertragen und sicher gespeichert.
                    </p>
                  </div>
                </section>

                <section>
                  <h3 className="ki-title mb-3">4. Ihre Rechte</h3>
                  <div className="space-y-3">
                    <p>
                      Sie haben jederzeit das Recht, die Löschung Ihres Kontos und Ihrer gespeicherten personenbezogenen Daten zu verlangen, soweit keine gesetzlichen Aufbewahrungsfristen entgegenstehen.
                    </p>
                  </div>
                </section>

                <section>
                  <h3 className="ki-title mb-3">5. Speicherdauer</h3>
                  <div className="space-y-3">
                    <p>
                      Ihre Daten werden gespeichert, solange Sie ein aktives Konto bei uns haben.
                    </p>
                    <p>
                      Nach Löschung Ihres Kontos werden Ihre personenbezogenen Daten gelöscht, soweit keine gesetzlichen Aufbewahrungsfristen bestehen.
                    </p>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
