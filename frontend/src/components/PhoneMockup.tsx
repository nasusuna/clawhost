"use client";

import { useState, useEffect } from "react";
import Image from "next/image";

const STEP_PATHS = [
  "/telegram-setup/tg-step1.jpg",
  "/telegram-setup/tg-step2a.jpg",
  "/telegram-setup/tg-step2.jpg",
  "/telegram-setup/tg-step3.jpg",
  "/telegram-setup/tg-step4.jpg",
  "/telegram-setup/tg-step5.jpg",
];

const STEP_LABELS = [
  "Search for @BotFather",
  "Open BotFather chat",
  "View available commands",
  "Send /newbot command",
  "Type /newbot",
  "Copy your bot token",
];

export default function PhoneMockup() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentStep((prev) => (prev + 1) % STEP_PATHS.length);
        setIsTransitioning(false);
      }, 400);
    }, currentStep === 5 ? 5000 : 3000);

    return () => clearInterval(interval);
  }, [currentStep]);

  const handleStepClick = (i: number) => {
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentStep(i);
      setIsTransitioning(false);
    }, 300);
  };

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="phone-shadow relative h-[580px] w-[280px] overflow-hidden rounded-[2.5rem] border-[3px] border-secondary bg-background">
        <div className="absolute left-1/2 top-0 z-10 h-6 w-28 -translate-x-1/2 rounded-b-2xl bg-background" />
        <div className="relative h-full w-full overflow-hidden rounded-[2.3rem]">
          <Image
            src={STEP_PATHS[currentStep]}
            alt={STEP_LABELS[currentStep]}
            fill
            className={`object-cover object-top transition-opacity duration-300 ${
              isTransitioning ? "opacity-0" : "opacity-100"
            }`}
            sizes="280px"
            unoptimized
          />
          {currentStep === 5 && !isTransitioning && (
            <div className="pointer-events-none absolute inset-0">
              <div className="absolute inset-0 bg-background/40" />
              <div
                className="absolute left-[6%] right-[10%] overflow-hidden rounded-lg"
                style={{ top: "62%", height: "14%" }}
              >
                <div className="animate-pulse absolute inset-0 rounded-lg border-2 border-primary bg-primary/20" />
              </div>
              <div
                className="absolute left-[8%] right-[12%] flex flex-col gap-0.5"
                style={{ top: "63%" }}
              >
                <span className="text-[7px] font-bold text-primary drop-shadow-lg">
                  Use this token to access the HTTP API:
                </span>
                <span className="text-[7px] font-mono font-bold text-primary drop-shadow-lg">
                  8648867798:AAG8_d7●●●●●●●●●●●●●●●●●●dBw
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col items-center gap-3">
        <p className="text-sm font-medium text-muted-foreground">
          {STEP_LABELS[currentStep]}
        </p>
        <div className="flex gap-1.5">
          {STEP_PATHS.map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleStepClick(i)}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === currentStep
                  ? "w-6 bg-primary"
                  : "w-2 bg-secondary hover:bg-muted-foreground"
              }`}
              aria-label={`Go to step ${i + 1}: ${STEP_LABELS[i]}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
