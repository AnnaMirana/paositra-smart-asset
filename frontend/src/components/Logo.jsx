import { useState } from 'react'

// Affiche /public/logo-paositra.png s'il existe ; sinon une pastille bleue et jaune.
// (Voir public/LISEZ-MOI-LOGO.txt)
export default function Logo({ clair = false }) {
    const [imageOk, setImageOk] = useState(true);
    return (
        <div className={`logo ${clair ? 'logo-clair' : ''}`}>
            {imageOk ? (
                <img src="/logo-paositra.png" alt="Paositra Malagasy" onError={() => setImageOk(false)} />
            ) : (
                <span className="logo-mark" aria-hidden="true">
                    P
                </span>
            )}
            <div className="logo-text">
                <strong>PAOSITRA</strong>
                <span>SMART ASSET</span>
            </div>
        </div>
    );
}