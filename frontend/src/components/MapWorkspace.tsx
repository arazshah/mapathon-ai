"use client";

import {
  FormEvent,
  KeyboardEvent,
  useMemo,
  useRef,
  useState,
} from "react";

import type {
  FeatureCollection,
  Geometry,
} from "geojson";

import MapView, {
  MapPlace,
} from "./MapView";


interface UserLocation {
  latitude: number;
  longitude: number;
}

interface QueryMetrics {
  distance_meters?: number;
  duration_seconds?: number;
  total_places?: number;
  extra?: Record<string, unknown>;
}

interface QueryResponse {
  success: boolean;
  operation?: string;
  message?: string;
  answer?: string;
  places?: MapPlace[];
  geojson?: FeatureCollection<Geometry> | null;
  metrics?: QueryMetrics | null;
  tools_used?: string[];
  routes?: unknown[];
  needs_clarification?: boolean;
  clarification_question?: string | null;
  detail?: unknown;
}

const EXAMPLES = [
  "رستوران‌های نزدیک میدان ونک را پیدا کن",
  "از میدان آزادی تا میدان ونک مسیر بده",
  "نزدیک‌ترین بیمارستان به موقعیت من کجاست؟",
  "ایستگاه‌های مترو نزدیک میدان انقلاب",
];

function normalizeApiBase(value: string): string {
  return value.replace(/\/+$/, "");
}

function formatDistance(
  meters?: number,
): string | null {
  if (
    typeof meters !== "number" ||
    !Number.isFinite(meters)
  ) {
    return null;
  }

  if (meters < 1000) {
    return `${Math.round(
      meters,
    ).toLocaleString("fa-IR")} متر`;
  }

  return `${(meters / 1000).toLocaleString(
    "fa-IR",
    {
      maximumFractionDigits: 1,
    },
  )} کیلومتر`;
}

function formatDuration(
  seconds?: number,
): string | null {
  if (
    typeof seconds !== "number" ||
    !Number.isFinite(seconds)
  ) {
    return null;
  }

  const minutes = Math.max(
    1,
    Math.round(seconds / 60),
  );

  if (minutes < 60) {
    return `${minutes.toLocaleString(
      "fa-IR",
    )} دقیقه`;
  }

  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;

  return `${hours.toLocaleString(
    "fa-IR",
  )} ساعت${
    remaining
      ? ` و ${remaining.toLocaleString(
          "fa-IR",
        )} دقیقه`
      : ""
  }`;
}

export default function MapWorkspace() {
  const requestControllerRef =
    useRef<AbortController | null>(null);
  const [query, setQuery] = useState("");
  const [result, setResult] =
    useState<QueryResponse | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [userLocation, setUserLocation] =
    useState<UserLocation | null>(null);

  const [locating, setLocating] =
    useState(false);

  const [selectedPlace, setSelectedPlace] =
    useState<MapPlace | null>(null);

  const apiBase = useMemo(
    () =>
      normalizeApiBase(
        import.meta.env.VITE_API_URL ??
          "http://127.0.0.1:8000",
      ),
    [],
  );

  async function submitQuery(
    event?: FormEvent,
  ) {
    event?.preventDefault();

    const normalizedQuery = query.trim();

    if (!normalizedQuery || loading) {
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedPlace(null);
    requestControllerRef.current?.abort();

    const controller = new AbortController();
    requestControllerRef.current = controller;

    try {
      const response = await fetch(
        `${apiBase}/api/v1/query`,
        {
          signal: controller.signal,
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            query: normalizedQuery,
            context: {
              language: "fa",
              timezone: "Asia/Tehran",
              ...(userLocation
                ? {
                    user_location:
                      userLocation,
                  }
                : {}),
            },
          }),
        },
      );

      const rawText = await response.text();

      let data: QueryResponse;

      try {
        data = JSON.parse(rawText);
      } catch {
        throw new Error(
          "پاسخ دریافتی از سرور JSON معتبر نیست.",
        );
      }

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : `خطای سرور با کد ${response.status}`;

        throw new Error(detail);
      }

      setResult(data);

      if (
        !data.success &&
        !data.needs_clarification
      ) {
        setError(
          data.message ??
            "نتیجه‌ای برای این پرس‌وجو پیدا نشد.",
        );
      }
    } catch (requestError) {
      if (
        requestError instanceof DOMException &&
        requestError.name === "AbortError"
      ) {
        return;
      }

      const message =
        requestError instanceof Error
          ? requestError.message
          : "اتصال به سرور برقرار نشد.";

      setError(message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function requestUserLocation() {
    if (!navigator.geolocation) {
      setError(
        "مرورگر شما از موقعیت مکانی پشتیبانی نمی‌کند.",
      );
      return;
    }

    setLocating(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          latitude:
            position.coords.latitude,
          longitude:
            position.coords.longitude,
        });

        setLocating(false);
      },
      () => {
        setError(
          "دسترسی به موقعیت مکانی ممکن نشد. لطفاً اجازه دسترسی مرورگر را بررسی کنید.",
        );
        setLocating(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 60000,
      },
    );
  }

  function handleTextareaKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      void submitQuery();
    }
  }

  const distance = formatDistance(
    result?.metrics?.distance_meters,
  );

  const duration = formatDuration(
    result?.metrics?.duration_seconds,
  );

  const places = result?.places ?? [];

  const clarification =
    result?.needs_clarification
      ? result.clarification_question ??
        result.message
      : null;

  return (
    <main className="workspace">
      <MapView
        geojson={result?.geojson}
        selectedPlace={selectedPlace}
        loading={loading}
      />

      <section
        className="query-panel"
        aria-label="پرس‌وجوی مکانی"
      >
        {loading && (
          <div className="analysis-status" role="status">
            <span className="analysis-spinner" />
            <span>
              در حال تحلیل درخواست شما روی نقشه...
            </span>
          </div>
        )}

        <div className="query-heading">
          <div>
            <span className="eyebrow">
              هوش مصنوعی مکانی
            </span>

            <h1>
              کجا را می‌خواهید پیدا کنید؟
            </h1>
          </div>

          <div
            className="online-status"
            title="سامانه آماده دریافت پرس‌وجو است"
          >
            <span />
            آماده
          </div>
        </div>

        <form
          className="query-form"
          onSubmit={submitQuery}
        >
          <textarea
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            onKeyDown={
              handleTextareaKeyDown
            }
            placeholder="مثلاً: از موقعیت من تا فرودگاه مهرآباد با خودرو مسیر بده"
            rows={2}
            disabled={loading}
            aria-label="متن پرس‌وجوی مکانی"
          />

          <div className="query-actions">
            <button
              type="button"
              className={
                userLocation
                  ? "location-button active"
                  : "location-button"
              }
              onClick={requestUserLocation}
              disabled={locating}
            >
              <svg
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M12 21s6-5.1 6-11a6 6 0 1 0-12 0c0 5.9 6 11 6 11Z" />
                <circle
                  cx="12"
                  cy="10"
                  r="2.25"
                />
              </svg>

              {locating
                ? "در حال دریافت..."
                : userLocation
                  ? "موقعیت فعال است"
                  : "موقعیت من"}
            </button>

            <button
              type="submit"
              className="submit-button"
              disabled={
                loading || !query.trim()
              }
            >
              {loading ? (
                <>
                  <span className="spinner light" />
                  در حال بررسی
                </>
              ) : (
                <>
                  جست‌وجو
                  <svg
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path d="m9 18 6-6-6-6" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </form>

        {!result && !error && (
          <div className="examples">
            {EXAMPLES.map((example) => (
              <button
                type="button"
                key={example}
                onClick={() =>
                  setQuery(example)
                }
              >
                {example}
              </button>
            ))}
          </div>
        )}

        {userLocation && (
          <div className="location-notice">
            <span />
            موقعیت شما با موفقیت دریافت شد.
          </div>
        )}
      </section>

      {(result || error) && (
        <section
          className="result-panel"
          aria-live="polite"
        >
          <div className="result-header">
            <div>
              <span className="result-label">
                نتیجه تحلیل
              </span>

              <h2>
                {error
                  ? "امکان انجام درخواست نبود"
                  : result?.operation ===
                      "route"
                    ? "مسیر پیشنهادی"
                    : "نتایج مکانی"}
              </h2>
            </div>

            <button
              type="button"
              className="close-result"
              aria-label="بستن نتیجه"
              onClick={() => {
                setResult(null);
                setError(null);
                setSelectedPlace(null);
              }}
            >
              ×
            </button>
          </div>

          {error ? (
            <p className="error-message">
              {error}
            </p>
          ) : clarification ? (
            <div className="clarification">
              <p>{clarification}</p>

              {!userLocation && (
                <button
                  type="button"
                  onClick={
                    requestUserLocation
                  }
                >
                  دریافت موقعیت من
                </button>
              )}
            </div>
          ) : (
            <>
              <p className="result-message">
                {result?.message ??
                  result?.answer ??
                  "نتیجه روی نقشه نمایش داده شد."}
              </p>

              {(distance || duration) && (
                <div className="metrics">
                  {distance && (
                    <div>
                      <span>فاصله</span>
                      <strong>
                        {distance}
                      </strong>
                    </div>
                  )}

                  {duration && (
                    <div>
                      <span>زمان تقریبی</span>
                      <strong>
                        {duration}
                      </strong>
                    </div>
                  )}
                </div>
              )}

              {places.length > 0 && (
                <div className="places-list">
                  {places.map(
                    (place, index) => (
                      <button
                        type="button"
                        key={`${
                          place.title ??
                          place.name ??
                          "place"
                        }-${index}`}
                        onClick={() =>
                          setSelectedPlace(
                            place,
                          )
                        }
                      >
                        <span className="place-number">
                          {(
                            index + 1
                          ).toLocaleString(
                            "fa-IR",
                          )}
                        </span>

                        <span>
                          <strong>
                            {place.title ??
                              place.name ??
                              `مکان ${
                                index + 1
                              }`}
                          </strong>

                          {place.address && (
                            <small>
                              {
                                place.address
                              }
                            </small>
                          )}
                        </span>
                      </button>
                    ),
                  )}
                </div>
              )}
            </>
          )}
        </section>
      )}
    </main>
  );
}
