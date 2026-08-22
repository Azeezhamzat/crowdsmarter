import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router";

type HeroVideoProps = {
  eyebrow: string;
  title: ReactNode;
  lead: string;
  primaryCta: { label: string; href: string };
  secondaryCta: { label: string; href: string };
  trustItems: string[];
};

export function HeroVideo({ eyebrow, title, lead, primaryCta, secondaryCta, trustItems }: HeroVideoProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(true);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      video.pause();
      setIsPlaying(false);
      return;
    }
    const playPromise = video.play();
    if (playPromise?.catch) {
      playPromise.catch(() => setIsPlaying(false));
    }
  }, []);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    } else {
      video.pause();
      setIsPlaying(false);
    }
  };

  return (
    <section className="hero hero--video" aria-labelledby="hero-title">
      <div className="hero__media" aria-hidden="true">
        <video ref={videoRef} className="hero__video" muted loop playsInline preload="metadata" poster="/hero-poster.jpg">
          <source src="/hero-mobile.mp4" type="video/mp4" media="(max-width: 767px)" />
          <source src="/hero-desktop.mp4" type="video/mp4" />
        </video>
      </div>
      <div className="hero__overlay" aria-hidden="true" />
      <div className="hero__copy hero__copy--video">
        <p className="public-eyebrow public-eyebrow--light">{eyebrow}</p>
        <h1 id="hero-title">{title}</h1>
        <p className="hero__lead hero__lead--video">{lead}</p>
        <div className="hero__actions">
          <Link className="public-button public-button--light public-button--large" to={primaryCta.href}>
            {primaryCta.label}
          </Link>
          <a className="public-button public-button--ghost public-button--large" href={secondaryCta.href}>
            {secondaryCta.label}
          </a>
        </div>
        <div className="hero__trust-row hero__trust-row--video">
          {trustItems.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </div>
      <button className="hero__video-control" type="button" aria-pressed={!isPlaying} onClick={togglePlay}>
        {isPlaying ? "Pause video" : "Play video"}
      </button>
    </section>
  );
}
