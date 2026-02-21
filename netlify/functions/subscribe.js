/**
 * Netlify serverless function — proxies email subscriptions to the Beehiiv API.
 * Keeps the API key server-side so it's never exposed to the client.
 *
 * Env vars (set in Netlify dashboard):
 *   BEEHIIV_API_KEY          — Beehiiv API v2 key
 *   BEEHIIV_PUBLICATION_ID   — Publication ID (pub_...)
 */

export default async function handler(request) {
  if (request.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  const { BEEHIIV_API_KEY, BEEHIIV_PUBLICATION_ID } = process.env;

  if (!BEEHIIV_API_KEY || !BEEHIIV_PUBLICATION_ID) {
    console.error("Missing BEEHIIV_API_KEY or BEEHIIV_PUBLICATION_ID env vars");
    return new Response(
      JSON.stringify({ error: "Server configuration error" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  let email;
  try {
    const body = await request.json();
    email = body.email;
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return new Response(JSON.stringify({ error: "Valid email is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const res = await fetch(
      `https://api.beehiiv.com/v2/publications/${BEEHIIV_PUBLICATION_ID}/subscriptions`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${BEEHIIV_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          reactivate_existing: true,
          send_welcome_email: false,
        }),
      }
    );

    if (!res.ok) {
      const err = await res.text();
      console.error("Beehiiv API error:", res.status, err);
      return new Response(
        JSON.stringify({ error: "Subscription failed. Please try again." }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("Beehiiv API request failed:", err);
    return new Response(
      JSON.stringify({ error: "Subscription failed. Please try again." }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }
}
