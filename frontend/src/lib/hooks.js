// hooks.js (Version corrigée)
import { useEffect, useRef, useState } from 'react';

export function useLoad(chargeur, deps = []) {
  const [etat, setEtat] = useState({ loading: true, data: null, error: null });
  const [top, setTop] = useState(0);
  const dernier = useRef(chargeur);
  dernier.current = chargeur;

  useEffect(() => {
    let annule = false;
    setEtat((e) => ({ ...e, loading: true, error: null }));
    dernier
      .current()
      .then((data) => {
        if (!annule) setEtat({ loading: false, data, error: null });
      })
      .catch((error) => {
        if (!annule) setEtat((e) => ({ loading: false, data: e.data, error }));
      });
    return () => {
      annule = true;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [top, ...deps]);

  return { ...etat, reload: () => setTop((t) => t + 1) };
}