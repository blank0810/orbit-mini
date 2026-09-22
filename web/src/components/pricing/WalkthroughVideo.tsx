"use client";

import { useEffect, useRef, useState } from "react";

const SRC = "/orbit-walkthrough.mp4";
const POSTER = "/orbit-walkthrough.jpg";
const CAPTIONS = "/orbit-walkthrough.vtt";
const RUNTIME = "1 min 37 sec";

// The narration, verbatim. A transcript is the media alternative for anyone who cannot or
// would rather not watch, and it is the only part of the video a search engine can read.
const TRANSCRIPT = [
  "Orbit Mini. A working slice of a client subscription dashboard.",
  "It opens on ScaleSage's own pricing. Two plans, not a comparison matrix. Pro is marked recommended, so the choice is yes or no.",
  "Signing up takes four fields. The password rule is stated up front, rather than revealed on failure. Submitting goes straight to Stripe.",
  "Checkout is Stripe hosted. No card details ever touch this system, so there is no card data to defend. Note the sandbox badge. This is test mode throughout.",
  "Then it waits. Payment succeeding and the webhook landing are different moments, so this screen polls rather than assuming.",
  "Here is what the brief asked for. One page: the plan, the status, the renewal date. Status carries an icon and a word, never colour alone.",
  "Plans switch either direction, prorated. Cancelling waits until the end of the period you already paid for.",
  "And it was built for a phone first, at three hundred and ninety pixels.",
  "A Flutter component, on a real phone, calling the same API as the web dashboard. Every state reviewable on its own.",
  "FastAPI, Postgres, Next.js, Flutter, Docker, and a Cloudflare Tunnel. Live now.",
];

export function WalkthroughVideo() {
  const [playing, setPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  // The button that had focus is gone the moment it is clicked, and focus would fall back
  // to <body>. Moving it onto the player keeps a keyboard user where they just acted.
  useEffect(() => {
    if (playing) videoRef.current?.focus();
  }, [playing]);

  return (
    <section aria-labelledby="walkthrough-heading" className="mt-16">
      <h2
        id="walkthrough-heading"
        className="text-2xl font-bold tracking-tight sm:text-3xl"
      >
        See it working
      </h2>
      <p className="mt-3 max-w-xl text-text-2">
        Sign-up, Stripe checkout, the webhook landing, and the same subscription
        on a phone. {RUNTIME}, narrated.
      </p>

      {/* Same rounded-2xl / border / surface language as the plan cards above, so the
          section reads as one region of the same page rather than an embed dropped in
          (Gestalt: similarity and common region). */}
      <div className="mt-6 overflow-hidden rounded-2xl border border-border bg-surface">
        <div className="relative aspect-video">
          {playing ? (
            <video
              ref={videoRef}
              src={SRC}
              poster={POSTER}
              controls
              autoPlay
              playsInline
              preload="auto"
              className="absolute inset-0 size-full bg-bg"
            >
              {/* On by default. The cue file anchors every cue at line:-2, which seats
                  it just above the scene titles burned into the bottom of the frame
                  rather than on top of them -- or, as a first attempt did, in the middle
                  of the picture. Reasoning is in the NOTE block of the .vtt. */}
              <track
                kind="captions"
                src={CAPTIONS}
                srcLang="en"
                label="English"
                default
              />
            </video>
          ) : (
            <button
              type="button"
              onClick={() => setPlaying(true)}
              // The whole 16:9 frame is the target, not a 48px glyph inside it
              // (Fitts's Law). The visible circle is only the signifier.
              aria-label={`Play the walkthrough, ${RUNTIME}`}
              className="group absolute inset-0 flex cursor-pointer items-center justify-center focus-visible:outline-offset-[-4px]"
            >
              {/* eslint-disable-next-line @next/next/no-img-element -- a fixed-size still
                  served from /public gains nothing from the optimizer, and next/image
                  would put sharp on the critical path inside the standalone container. */}
              <img
                src={POSTER}
                alt=""
                className="absolute inset-0 size-full object-cover"
              />
              {/* A scrim, so the control keeps its contrast over whatever the frame
                  happens to show, and so the still reads as "not playing yet". */}
              <span className="absolute inset-0 bg-bg/45 transition-colors group-hover:bg-bg/35" />

              <span className="relative flex size-20 items-center justify-center rounded-full bg-accent text-on-accent transition-colors group-hover:bg-accent/90">
                <svg
                  aria-hidden="true"
                  viewBox="0 0 24 24"
                  className="size-8 translate-x-0.5"
                  fill="currentColor"
                >
                  <path d="M8 5.14v13.72a1 1 0 0 0 1.54.84l10.3-6.86a1 1 0 0 0 0-1.68L9.54 4.3A1 1 0 0 0 8 5.14Z" />
                </svg>
              </span>
            </button>
          )}
        </div>
      </div>

      <details className="group mt-4">
        <summary className="inline-flex min-h-11 cursor-pointer items-center text-sm text-text-3 underline underline-offset-4 hover:text-text-2">
          Read the transcript instead
        </summary>
        <div className="mt-3 space-y-3 border-l border-border pl-4 text-sm text-text-2">
          {TRANSCRIPT.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
      </details>
    </section>
  );
}
