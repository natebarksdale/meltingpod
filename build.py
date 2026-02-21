#!/usr/bin/env python3
"""
Build script for The Melting Pod website.

Reads episode data from data/episodes.json and generates static HTML pages.
Templates live in templates/ as plain HTML with {{variable}} placeholders.

Usage:
    python build.py          # Build all pages
    python build.py --clean  # Remove generated episode pages, then build
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

SITE_URL = "https://meltingpod.org"

# --- Beehiiv newsletter integration ---
# 1. Create a free account at beehiiv.com
# 2. Set your publication ID below (Settings > Integrations > API)
# 3. Set your subscribe page URL (e.g. "https://meltingpod.beehiiv.com/subscribe")
BEEHIIV_PUBLICATION_ID = "YOUR_PUBLICATION_ID"
BEEHIIV_SUBSCRIBE_URL = "https://meltingpod.beehiiv.com/subscribe"
TEMPLATES_DIR = ROOT / "templates"


# --- SEO helpers ---

def build_jsonld(data):
    """Return a <script> tag containing JSON-LD structured data."""
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def parse_episode_date(date_str):
    """Convert 'February 10, 2026' to a datetime object."""
    return datetime.strptime(date_str, "%B %d, %Y")


def duration_to_iso(duration_str):
    """Convert '69 min' to 'PT69M'."""
    minutes = int(duration_str.split()[0])
    return f"PT{minutes}M"


def smart_truncate(text, max_length=155):
    """Truncate at sentence or word boundary instead of mid-word."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_period = truncated.rfind('. ')
    if last_period > max_length * 0.5:
        return truncated[:last_period + 1]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space] + "\u2026"
    return truncated + "\u2026"


def build_podcast_series_jsonld():
    """JSON-LD for PodcastSeries, included on every page."""
    return {
        "@context": "https://schema.org",
        "@type": "PodcastSeries",
        "name": "The Melting Pod",
        "description": "Stories about our dysfunctional immigration system and where we go from here.",
        "url": f"{SITE_URL}/",
        "image": f"{SITE_URL}/The_Melting_Pod_Podcast_Logo_3000.png",
        "author": [
            {"@type": "Person", "name": "Claire Trickler-McNulty"},
            {"@type": "Person", "name": "Amanda Baran"},
            {"@type": "Person", "name": "Doug Rand"},
        ],
        "webFeed": f"{SITE_URL}/feed.xml",
    }

def load_episodes():
    with open(DATA_DIR / "episodes.json", "r") as f:
        return json.load(f)

def read_template(name):
    with open(TEMPLATES_DIR / name, "r") as f:
        return f.read()

def render(template, context):
    """Simple {{variable}} replacement. Supports {{variable}} syntax."""
    def replacer(match):
        key = match.group(1).strip()
        val = context.get(key, match.group(0))
        if val is None:
            return ""
        return str(val)
    return re.sub(r"\{\{(.+?)\}\}", replacer, template)

def build_nav(active_page):
    """Generate nav links with correct active state."""
    pages = [
        ("index.html", "Home"),
        ("episodes.html", "Episodes"),
        ("about.html", "About"),
        ("contact.html", "Contact"),
    ]
    nav_links = []
    mobile_links = []
    for href, label in pages:
        active = ' nav__link--active' if href == active_page else ''
        mobile_active = ' mobile-menu__link--active' if href == active_page else ''
        nav_links.append(f'        <a href="{href}" class="nav__link{active}">{label}</a>')
        mobile_links.append(f'      <a href="{href}" class="mobile-menu__link{mobile_active}">{label}</a>')
    return "\n".join(nav_links), "\n".join(mobile_links)

def build_head(title, description, *, page_url="", og_image="", og_type="website", published_date="", jsonld=None):
    og_img = f"{SITE_URL}/{og_image}" if og_image else f"{SITE_URL}/The_Melting_Pod_Podcast_Logo_3000.png"
    canonical = f"{SITE_URL}/{page_url}" if page_url else SITE_URL

    # Article meta (for episode pages)
    article_meta = ""
    if published_date:
        article_meta = f'\n  <meta property="article:published_time" content="{published_date}">'

    # JSON-LD blocks
    jsonld_html = ""
    if jsonld:
        jsonld_html = "\n  " + "\n  ".join(build_jsonld(block) for block in jsonld)

    return f'''<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og_img}">
  <meta property="og:site_name" content="The Melting Pod">{article_meta}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_img}">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" type="application/rss+xml" title="The Melting Pod" href="{SITE_URL}/feed.xml">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="icon" type="image/x-icon" sizes="16x16 32x32 48x48 64x64 128x128 256x256" href="favicon.ico">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300..700;1,9..40,300..700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles7.css">{jsonld_html}
</head>'''

def build_nav_html(active_page):
    nav_links, mobile_links = build_nav(active_page)
    return f'''  <a href="#main" class="skip-link">Skip to content</a>

  <!-- Navigation -->
  <nav class="nav" id="nav">
    <div class="nav__inner">
      <a href="index.html" class="nav__logo">
        <img src="TMP_text_horiz_black.svg" alt="The Melting Pod" class="nav__logotype">
        <img src="TMP_Logo_animated_melt.svg" alt="" class="nav__logo-icon">
      </a>
      <div class="nav__links" id="navLinks">
{nav_links}
      </div>
      <div class="nav__actions">
        <a href="episodes.html" class="btn btn--small btn--accent">Listen Now</a>
        <button class="nav__burger" id="navBurger" aria-label="Toggle menu" aria-expanded="false">
          <span></span><span></span><span></span>
        </button>
      </div>
    </div>
  </nav>

  <!-- Mobile Menu -->
  <div class="mobile-menu" id="mobileMenu" aria-hidden="true">
    <div class="mobile-menu__inner">
{mobile_links}
      <div class="mobile-menu__cta">
        <a href="episodes.html" class="btn btn--accent btn--full">Listen Now</a>
      </div>
    </div>
  </div>'''

def build_footer(include_newsletter=True):
    newsletter = ""
    if include_newsletter:
        newsletter = f'''
      <div class="footer__newsletter" id="newsletter">
        <div class="footer__newsletter-text">
          <h4 class="footer__newsletter-title">Stay in the loop</h4>
          <p class="footer__newsletter-desc">Get updates on new episodes and immigration news.</p>
        </div>
        <form class="footer__newsletter-form" action="{BEEHIIV_SUBSCRIBE_URL}" method="get" target="beehiiv-frame">
          <input type="email" name="email" class="footer__newsletter-input" placeholder="Your email address" required>
          <button type="submit" class="btn btn--accent footer__newsletter-btn">Subscribe</button>
        </form>
        <iframe name="beehiiv-frame" style="display:none" aria-hidden="true" tabindex="-1"></iframe>
        <div class="footer__newsletter-success" aria-live="polite"></div>
      </div>'''

    return f'''  <!-- Footer -->
  <footer class="footer">
    <div class="container">
      <div class="footer__inner">
        <div class="footer__brand">
          <div class="footer__logo-lockup scroll-reveal">
            <img src="TMP_text_horiz_white.svg" alt="The Melting Pod" class="footer__logotype">
            <img src="TMP_Logo_2-9_animated.svg" alt="" class="footer__logo-icon">
          </div>
          <p class="footer__tagline">Stories about our dysfunctional immigration system and where we go from here.</p>
        </div>
        <div class="footer__links">
          <div class="footer__col">
            <h4 class="footer__col-title">Podcast</h4>
            <a href="episodes.html">Episodes</a>
            <a href="about.html">About</a>
            <a href="contact.html">Contact</a>
          </div>
          <div class="footer__col">
            <h4 class="footer__col-title">Listen</h4>
            <a href="#">Apple Podcasts</a>
            <a href="#">Spotify</a>
            <a href="https://www.youtube.com/@themeltingpod">YouTube</a>
            <a href="feed.xml">RSS Feed</a>
          </div>
          <div class="footer__col">
            <h4 class="footer__col-title">Connect</h4>
            <a href="https://bsky.app/profile/meltingpod.bsky.social">Bluesky</a>
            <a href="https://www.instagram.com/meltingpodshow">Instagram</a>
            <a href="contact.html">Tips &amp; Press</a>
          </div>
        </div>
      </div>{newsletter}
      <div class="footer__bottom">
        <span>&copy; 2026 The Melting Pod. All rights reserved.</span>
      </div>
    </div>
  </footer>'''

# --- Page builders ---

def build_episode_card(ep, with_image=True):
    """Build an episode card for the homepage recent grid."""
    img_html = ""
    img_class = ""
    if with_image and ep.get("image"):
        img_html = f'\n          <img src="{ep["image"]}" alt="{ep.get("image_alt", ep["title"])}" class="episode-card__img">\n          <div class="episode-card__overlay"></div>'
        img_class = " episode-card--has-img"

    clock_svg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'

    return f'''        <a href="episode-{ep['slug']}.html" class="episode-card{img_class} scroll-reveal">{img_html}
          <div class="episode-card__content">
            <span class="episode-card__date">{ep['date']}</span>
            <h3 class="episode-card__title">{ep['title']}</h3>
            <p class="episode-card__desc">{ep['description']}</p>
            <span class="episode-card__meta">
              {clock_svg}
              {ep['duration']}
            </span>
          </div>
        </a>'''

def build_episode_row(ep):
    """Build an episode row for the episodes list page (legacy)."""
    return f'''        <a href="episode-{ep['slug']}.html" class="episode-row scroll-reveal">
          <div class="episode-row__body">
            <h2 class="episode-row__title">{ep['title']}</h2>
            <span class="episode-row__date">{ep['date']} &middot; {ep['duration']}</span>
          </div>
          <div class="episode-row__meta">
            <div class="episode-row__play">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            </div>
          </div>
        </a>'''


def build_episode_archive_card(ep):
    """Build an episode card for the redesigned episodes archive."""
    has_image = ep.get("image")
    img_class = " episode-archive-card--has-img" if has_image else ""

    # Image markup
    img_html = ""
    if has_image:
        img_html = f'''
          <div class="episode-archive-card__img-wrap">
            <img src="{ep['image']}" alt="{ep.get('image_alt', ep['title'])}" class="episode-archive-card__img">
            <div class="episode-archive-card__img-overlay"></div>
          </div>'''

    # Guest markup
    guest_html = ""
    if ep.get("guest"):
        g = ep["guest"]
        if g.get("image"):
            guest_avatar = f'<img src="{g["image"]}" alt="{g["name"]}" class="episode-archive-card__guest-avatar" style="width:24px;height:24px;border-radius:50%;object-fit:cover;">'
        else:
            guest_avatar = f'<div class="episode-archive-card__guest-avatar">{g["initials"]}</div>'
        guest_html = f'''
            <div class="episode-archive-card__guest">
              {guest_avatar}
              <span>with {g['name']}</span>
            </div>'''

    # Clock icon
    clock_svg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'

    return f'''        <a href="episode-{ep['slug']}.html" class="episode-archive-card{img_class} scroll-reveal">{img_html}
          <div class="episode-archive-card__play">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </div>
          <div class="episode-archive-card__body">
            <div class="episode-archive-card__meta">
              <span>{ep['date']}</span>
            </div>
            <h2 class="episode-archive-card__title">{ep['title']}</h2>
            <p class="episode-archive-card__desc">{ep['description']}</p>
            <div class="episode-archive-card__footer">
              {guest_html if guest_html else '<span></span>'}
              <span class="episode-archive-card__duration">{clock_svg} {ep['duration']}</span>
            </div>
          </div>
        </a>'''


def build_featured_episode(ep):
    """Build the featured/latest episode section for episodes page."""
    # Image
    img_src = ep.get("image") or "https://tile.loc.gov/storage-services/service/pnp/ds/11800/11826r.jpg"

    # No player in the featured card — it lives on the detail page
    player_html = ''

    # Guest
    guest_html = ""
    if ep.get("guest"):
        g = ep["guest"]
        if g.get("image"):
            featured_avatar = f'<img src="{g["image"]}" alt="{g["name"]}" class="episode-featured__guest-avatar" style="width:32px;height:32px;border-radius:50%;object-fit:cover;">'
        else:
            featured_avatar = f'<div class="episode-featured__guest-avatar">{g["initials"]}</div>'
        guest_html = f'''
          <div class="episode-featured__guest">
            {featured_avatar}
            <div class="episode-featured__guest-info">
              <span class="episode-featured__guest-label">Featuring </span>
              <span class="episode-featured__guest-name">{g['name']}</span>
            </div>
          </div>'''

    return f'''    <div class="episode-featured">
      <a href="episode-{ep['slug']}.html" class="episode-featured__card scroll-reveal">
        <div class="episode-featured__visual">
          <img src="{img_src}" alt="{ep.get('image_alt', ep['title'])}" class="episode-featured__img">
          <div class="episode-featured__overlay"></div>
          <span class="episode-featured__badge">Premiere Episode</span>
        </div>
        <div class="episode-featured__content">
          <div class="episode-featured__meta">
            <span>{ep['date']}</span>
            <span>&middot;</span>
            <span>{ep['duration']}</span>
          </div>
          <h2 class="episode-featured__title">{ep['title']}</h2>
          <p class="episode-featured__desc">{ep['description']}</p>
          <div class="episode-featured__actions">
            <span class="btn btn--outline">Listen Now</span>
          </div>
          {guest_html}
        </div>
      </a>
    </div>'''

def build_index(episodes):
    """Build the homepage."""
    latest = episodes[0]  # Premiere episode (list is chronological)
    recent = episodes[1:4]  # Next episodes in chronological order

    # Player embed
    if latest.get("megaphone_id"):
        player_html = f'''          <div class="latest__player latest__player--megaphone">
            <iframe frameborder="0" height="200" scrolling="no" src="https://playlist.megaphone.fm?e={latest['megaphone_id']}" width="100%" title="Listen: {latest['title']}" loading="lazy"></iframe>
          </div>'''
    else:
        player_html = '          <div class="latest__player latest__player--coming-soon"><p style="color: var(--steel); font-style: italic;">Player coming soon</p></div>'

    # Recent episode cards
    cards_html = "\n".join(build_episode_card(ep) for ep in recent)

    head = build_head(
        "The Melting Pod &mdash; Stories About Our Dysfunctional Immigration System",
        "Stories about our dysfunctional immigration system and where we go from here. A podcast by Claire Trickler-McNulty, Amanda Baran, and Doug Rand.",
        page_url="index.html",
        jsonld=[build_podcast_series_jsonld()],
    )
    nav = build_nav_html("index.html")
    footer = build_footer(include_newsletter=True)

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav}

  <!-- Hero -->
  <header class="hero">
    <div class="hero__bg">
      <!-- Historical immigration photos (public domain, Library of Congress) -->
      <div class="hero__photo hero__photo--1" aria-hidden="true">
        <!-- Immigrants arriving at Ellis Island, c. 1900s -->
        <img src="https://tile.loc.gov/storage-services/service/pnp/ds/11800/11826r.jpg" alt="" loading="eager">
      </div>
      <div class="hero__photo hero__photo--2" aria-hidden="true">
        <!-- Awaiting examination, Ellis Island, 1920 -->
        <img src="https://cdn.loc.gov/service/pnp/cph/3a30000/3a38000/3a38100/3a38144r.jpg" alt="" loading="eager">
      </div>
      <!-- Dark overlay for text readability -->
      <div class="hero__overlay"></div>
      <!-- Concentric circles pattern -->
      <svg class="hero__circles" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
        <g fill="none" stroke="rgba(232,145,58,0.05)" stroke-width="1">
          <circle cx="1050" cy="420" r="320"/>
          <circle cx="1050" cy="420" r="260"/>
          <circle cx="1050" cy="420" r="200"/>
          <circle cx="1050" cy="420" r="140"/>
          <circle cx="1050" cy="420" r="80"/>
          <circle cx="300" cy="700" r="180"/>
          <circle cx="300" cy="700" r="120"/>
          <circle cx="300" cy="700" r="60"/>
        </g>
      </svg>
    </div>
    <div class="hero__content">
      <h1 class="hero__title">
        <span class="hero__title-line">Stories about our</span>
        <span class="hero__title-line hero__title-line--italic">dysfunctional</span>
        <span class="hero__title-line">immigration system</span>
      </h1>
      <p class="hero__subtitle">Two decades under four presidents taught us how this system actually works &mdash; and why it doesn&rsquo;t. Now we&rsquo;re telling those stories.</p>
      <a href="episodes.html" class="btn btn--primary hero__cta-btn">
        <svg class="btn__icon" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        Listen to Trailer
      </a>
    </div>
    <!-- Host strip at bottom of hero -->
    <div class="hero__hosts-strip">
      <div class="hero__hosts-inner">
        <span class="hero__hosts-label">Your hosts</span>
        <div class="hero__host-cards">
          <a href="about.html" class="hero__host-card">
            <img src="claire.jpg" alt="Claire Trickler-McNulty" class="hero__host-avatar">
            <div class="hero__host-info">
              <span class="hero__host-name">Claire Trickler-McNulty</span>
            </div>
          </a>
          <a href="about.html" class="hero__host-card">
            <img src="amanda.jpg" alt="Amanda Baran" class="hero__host-avatar">
            <div class="hero__host-info">
              <span class="hero__host-name">Amanda Baran</span>
            </div>
          </a>
          <a href="about.html" class="hero__host-card">
            <img src="doug.jpeg" alt="Doug Rand" class="hero__host-avatar">
            <div class="hero__host-info">
              <span class="hero__host-name">Doug Rand</span>
            </div>
          </a>
        </div>
      </div>
    </div>
  </header>

  <!-- Subscribe strip -->
  <div class="subscribe-strip">
    <div class="subscribe-strip__inner">
      <span class="subscribe-strip__label">Subscribe:</span>
      <a href="#" class="subscribe-strip__link">
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
        Apple Podcasts
      </a>
      <a href="#" class="subscribe-strip__link">
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
        Spotify
      </a>
      <a href="https://www.youtube.com/@themeltingpod" class="subscribe-strip__link">
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
        YouTube
      </a>
      <a href="feed.xml" class="subscribe-strip__link">
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><circle cx="6.18" cy="17.82" r="2.18"/><path d="M4 4.44v2.83c7.03 0 12.73 5.7 12.73 12.73h2.83c0-8.59-6.97-15.56-15.56-15.56zm0 5.66v2.83c3.9 0 7.07 3.17 7.07 7.07h2.83c0-5.47-4.43-9.9-9.9-9.9z"/></svg>
        RSS
      </a>
      <a href="#newsletter" class="subscribe-strip__link">
        <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
        Newsletter
      </a>
    </div>
  </div>

  <!-- Main content -->
  <main id="main">

  <!-- Latest Episode -->
  <section class="latest">
    <div class="container">
      <div class="section-label">Premiere Episode</div>
      <div class="latest__card scroll-reveal">
        <div class="latest__meta">
          <span class="latest__date">{latest['date']}</span>
          <span class="latest__duration">{latest['duration']}</span>
        </div>
        <h2 class="latest__title">{latest['title']}</h2>
        <p class="latest__desc">{latest['description']}</p>
{player_html}
        <div class="latest__actions">
          <a href="episode-{latest['slug']}.html" class="btn btn--outline">Episode Notes &amp; Chapters</a>
          <button class="share-btn" title="Share episode">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
          </button>
        </div>
      </div>
    </div>
  </section>

  <!-- Recent Episodes -->
  <section class="recent">
    <div class="container">
      <div class="recent__header">
        <div class="section-label">Recent Episodes</div>
        <a href="episodes.html" class="recent__all">View all episodes&ensp;&rarr;</a>
      </div>
      <div class="recent__grid">
{cards_html}
      </div>
    </div>
  </section>


  <!-- Subscribe CTA -->
  <section class="subscribe-cta">
    <div class="container">
      <div class="subscribe-cta__inner scroll-reveal">
        <div class="subscribe-cta__text">
          <h2 class="subscribe-cta__title">Never miss an episode</h2>
          <p class="subscribe-cta__desc">New stories coming soon. Subscribe wherever you listen.</p>
        </div>
        <div class="subscribe-cta__buttons">
          <a href="#" class="platform-btn">Apple Podcasts</a>
          <a href="#" class="platform-btn">Spotify</a>
          <a href="https://www.youtube.com/@themeltingpod" class="platform-btn">YouTube</a>
          <a href="feed.xml" class="platform-btn">RSS Feed</a>
          <a href="#newsletter" class="platform-btn">Newsletter</a>
        </div>
      </div>
    </div>
  </section>

  </main>

{footer}

  <script src="main7.js"></script>
</body>
</html>'''


def build_episodes_page(episodes):
    """Build the episodes listing page."""
    # Featured episode (latest)
    latest = episodes[0]
    featured_html = build_featured_episode(latest)

    # Archive cards (all except latest)
    archive_episodes = episodes[1:]
    cards_html = "\n\n".join(build_episode_archive_card(ep) for ep in archive_episodes)

    head = build_head(
        "Episodes &mdash; The Melting Pod",
        "All episodes of The Melting Pod. Listen to stories about our dysfunctional immigration system.",
        page_url="episodes.html",
        jsonld=[build_podcast_series_jsonld()],
    )
    nav = build_nav_html("episodes.html")
    footer = build_footer(include_newsletter=True)

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav}

  <main id="main">

  <!-- Page Header -->
  <header class="page-header page-header--has-img">
    <img src="https://tile.loc.gov/storage-services/service/pnp/ds/11800/11826r.jpg" alt="Immigrants arriving at Ellis Island, early 1900s" class="page-header__img">
    <div class="page-header__overlay"></div>
    <div class="container" style="position: relative; z-index: 1;">
      <h1 class="page-header__title">Episodes</h1>
      <p class="page-header__desc">Stories about immigration policy, told by the people who lived it.</p>
      <p class="page-header__desc"><em>New stories coming soon. Catch up on everything you've missed.</em></p>
      <div class="page-header__subscribe">
        <span class="page-header__subscribe-label">Subscribe:</span>
        <a href="#" class="platform-btn platform-btn--dark">Apple Podcasts</a>
        <a href="#" class="platform-btn platform-btn--dark">Spotify</a>
        <a href="https://www.youtube.com/@themeltingpod" class="platform-btn platform-btn--dark">YouTube</a>
        <a href="feed.xml" class="platform-btn platform-btn--dark">RSS Feed</a>
        <a href="#newsletter" class="platform-btn platform-btn--dark">Newsletter</a>
      </div>
    </div>
  </header>

  <!-- Episodes Archive -->
  <section class="episodes-archive">
    <div class="container">

{featured_html}

      <!-- Archive Grid -->
      <div class="archive-header">
        <h2 class="archive-header__title">All Episodes</h2>
        <span class="archive-header__count">{len(archive_episodes)} episodes</span>
      </div>

      <div class="episodes-grid">
{cards_html}
      </div>

    </div>
  </section>

  </main>

{footer}

  <script src="main7.js"></script>
</body>
</html>'''


def build_episode_top_nav(prev_ep, next_ep):
    """Build compact prev/next navigation row for the page header."""
    chevron_left = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="15 18 9 12 15 6"/></svg>'
    chevron_right = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="9 18 15 12 9 6"/></svg>'

    prev_link = ""
    if prev_ep:
        prev_link = f'<a href="episode-{prev_ep["slug"]}.html" class="ep-topnav__link" title="{prev_ep["title"]}">{chevron_left} Prev</a>'

    next_link = ""
    if next_ep:
        next_link = f'<a href="episode-{next_ep["slug"]}.html" class="ep-topnav__link" title="{next_ep["title"]}">Next {chevron_right}</a>'

    # Build the row: prev (optional) | All Episodes | next (optional)
    # Only show chevron on "All Episodes" when there's no prev link
    all_chevron = "" if prev_ep else chevron_left + " "
    parts = []
    if prev_link:
        parts.append(prev_link)
    parts.append(f'<a href="episodes.html" class="ep-topnav__link ep-topnav__link--all">{all_chevron}All Episodes</a>')
    if next_link:
        parts.append(next_link)

    sep = '<span class="ep-topnav__sep">/</span>'
    inner = sep.join(parts)

    return f'<nav class="ep-topnav" aria-label="Episode navigation">{inner}</nav>'


def build_episode_bottom_nav(prev_ep, next_ep):
    """Build 'Continue Listening' section with adjacent episode cards."""
    if not prev_ep and not next_ep:
        return ""

    clock_svg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'

    def card(ep, direction):
        chevron = '<polyline points="15 18 9 12 15 6"/>' if direction == "prev" else '<polyline points="9 18 15 12 9 6"/>'
        label = "Previous Episode" if direction == "prev" else "Next Episode"
        return f'''        <a href="episode-{ep['slug']}.html" class="ep-bottomnav__card scroll-reveal">
          <span class="ep-bottomnav__dir">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">{chevron}</svg>
            {label}
          </span>
          <h3 class="ep-bottomnav__title">{ep['title']}</h3>
          <p class="ep-bottomnav__desc">{ep['description']}</p>
          <span class="ep-bottomnav__meta">{ep['date']} &middot; {clock_svg} {ep['duration']}</span>
        </a>'''

    cards = []
    if prev_ep:
        cards.append(card(prev_ep, "prev"))
    if next_ep:
        cards.append(card(next_ep, "next"))

    single_class = " ep-bottomnav__grid--single" if len(cards) == 1 else ""
    cards_html = "\n".join(cards)

    return f'''
  <!-- Continue Listening -->
  <section class="ep-bottomnav">
    <div class="container">
      <div class="section-label">Continue Listening</div>
      <div class="ep-bottomnav__grid{single_class}">
{cards_html}
      </div>
    </div>
  </section>'''


def build_episode_detail(ep, prev_ep=None, next_ep=None):
    """Build an individual episode detail page."""
    # Player (single-episode embed supports ?start= for chapter seeking)
    if ep.get("megaphone_id"):
        player_html = f'''          <div class="episode-detail__player episode-detail__player--megaphone">
            <iframe id="megaphonePlayer" frameborder="0" height="200" scrolling="no" src="https://player.megaphone.fm/{ep['megaphone_id']}" width="100%" title="Listen: {ep['title']}" loading="lazy"></iframe>
          </div>'''
    else:
        player_html = '          <div class="episode-detail__player episode-detail__player--coming-soon"><p style="color: var(--steel); font-style: italic;">Player coming soon</p></div>'

    # Transcript
    if ep.get("transcript"):
        transcript_html = f'''
          <!-- Transcript -->
          <div class="transcript">
            <button class="transcript__toggle" id="transcriptToggle">
              <span>Full Transcript</span>
              <svg class="transcript__toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
            <div class="transcript__body" id="transcriptBody">
              <div class="transcript__content">
                {ep['transcript']}
              </div>
            </div>
          </div>'''
    else:
        transcript_html = ""

    # Summary (longer multi-paragraph description, replaces short description when present)
    if ep.get("summary"):
        summary_html = f'''          <div class="episode-detail__summary">
            {ep['summary']}
          </div>'''
    else:
        summary_html = ""

    # Chapters / Timestamps
    # TODO: Re-enable chapters once timestamps are finalized
    if False and ep.get("chapters"):
        def time_to_seconds(t):
            """Convert 'M:SS' or 'H:MM:SS' to total seconds."""
            parts = t.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

        def render_chapter(ch):
            return (
                f'<li class="chapters__item">'
                f'<button class="chapters__time" data-seconds="{time_to_seconds(ch["time"])}">{ch["time"]}</button>'
                f'<span class="chapters__title">{ch["title"]}</span>'
                f'</li>'
            )

        preview_count = 2
        all_chapters = ep["chapters"]
        total = len(all_chapters)

        if total <= preview_count + 1:
            # Not worth collapsing for 3 or fewer items
            chapter_items = "\n".join(f'                {render_chapter(ch)}' for ch in all_chapters)
            chapters_html = f'''          <div class="chapters">
            <h2 class="chapters__heading">In This Episode</h2>
            <ol class="chapters__list">
{chapter_items}
            </ol>
          </div>'''
        else:
            preview_items = "\n".join(f'                {render_chapter(ch)}' for ch in all_chapters[:preview_count])
            overflow_items = "\n".join(f'                  {render_chapter(ch)}' for ch in all_chapters[preview_count:])
            remaining = total - preview_count
            chapters_html = f'''          <div class="chapters" id="chaptersSection">
            <h2 class="chapters__heading">In This Episode</h2>
            <ol class="chapters__list">
              <div class="chapters__preview">
{preview_items}
              </div>
              <div class="chapters__overflow">
                <div class="chapters__overflow-inner">
{overflow_items}
                </div>
              </div>
            </ol>
            <button class="chapters__toggle" id="chaptersToggle" aria-expanded="false">
              <span class="chapters__toggle-text">Show all {total} chapters</span>
              <svg class="chapters__toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
          </div>'''
    else:
        chapters_html = ""

    # Guest sidebar card
    guest_html = ""
    if ep.get("guest"):
        g = ep["guest"]
        if g.get("image"):
            avatar_html = f'<img src="{g["image"]}" alt="{g["name"]}" class="sidebar-host__avatar">'
        else:
            avatar_html = f'<div class="sidebar-host__avatar" style="background: var(--slate); color: var(--silver); display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 600;">{g["initials"]}</div>'
        guest_html = f'''
          <div class="sidebar-card">
            <h3 class="sidebar-card__title">Guest</h3>
            <div class="sidebar-card__hosts">
              <div class="sidebar-host">
                {avatar_html}
                <div>
                  <div class="sidebar-host__name">{g['name']}</div>
                  <div class="sidebar-host__role">{g['role']}</div>
                </div>
              </div>
            </div>
          </div>'''

    # Learn More & Give More sections (main column)
    resources_main_html = ""
    if ep.get("resources"):
        learn_items = [r for r in ep["resources"] if r.get("category") == "learn"]
        give_items = [r for r in ep["resources"] if r.get("category") == "give"]
        # Fallback: if no categories, treat all as learn
        if not learn_items and not give_items:
            learn_items = ep["resources"]

        sections = []

        # Learn More section
        if learn_items:
            arrow_svg_learn = '<svg class="learn-more__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>'
            learn_cards = []
            for r in learn_items:
                meta_parts = []
                if r.get("source"):
                    meta_parts.append(f'<span class="learn-more__source">{r["source"]}</span>')
                if r.get("date"):
                    meta_parts.append(f'<span class="learn-more__date">{r["date"]}</span>')
                meta_html = "\n                    ".join(meta_parts)
                desc_html = f'\n                  <p class="learn-more__desc">{r["description"]}</p>' if r.get("description") else ""
                learn_cards.append(f'''              <a href="{r['url']}" class="learn-more__item" target="_blank" rel="noopener">
                <div class="learn-more__body">
                  <h4 class="learn-more__title">{r['title']}</h4>
                  <div class="learn-more__meta">
                    {meta_html}
                  </div>{desc_html}
                </div>
                {arrow_svg_learn}
              </a>''')
            learn_html = "\n".join(learn_cards)
            sections.append(f'''          <div class="episode-resources__section">
            <h3 class="episode-resources__heading">Learn More</h3>
            <p class="episode-resources__disclaimer">Amanda, Claire, and Doug express their own personal opinions on The Melting Pod. Read more about the topics in this episode:</p>
            <div class="learn-more__list">
{learn_html}
            </div>
          </div>''')

        # Give More section
        if give_items:
            national = [r for r in give_items if r.get("scope") == "national"]
            local = [r for r in give_items if r.get("scope") == "local"]
            # Items without scope go into national
            unscoped = [r for r in give_items if not r.get("scope")]
            national = national + unscoped

            arrow_svg_give = '<svg class="give-more__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>'
            groups = []
            for label, items in [("National", national), ("Local", local)]:
                if not items:
                    continue
                org_cards = []
                for r in items:
                    desc_html = f'\n                    <p class="give-more__desc">{r["description"]}</p>' if r.get("description") else ""
                    org_cards.append(f'''                <a href="{r['url']}" class="give-more__item" target="_blank" rel="noopener">
                  <div class="give-more__body">
                    <div class="give-more__name">{r['title']}</div>{desc_html}
                  </div>
                  {arrow_svg_give}
                </a>''')
                orgs_html = "\n".join(org_cards)
                groups.append(f'''            <div class="give-more__group">
              <h4 class="give-more__group-label">{label}</h4>
              <div class="give-more__list">
{orgs_html}
              </div>
            </div>''')

            groups_html = "\n".join(groups)
            sections.append(f'''          <div class="episode-resources__section">
            <h3 class="episode-resources__heading">Give More</h3>
            <p class="episode-resources__intro">Want to help build a more sane and humane immigration system? Support hardworking organizations like these:</p>
            <div class="give-more__groups">
{groups_html}
            </div>
          </div>''')

        if sections:
            sections_html = "\n\n".join(sections)
            resources_main_html = f'''
          <div class="episode-resources">
{sections_html}
          </div>'''

    # Legacy sidebar resources (for episodes without categorized resources)
    resources_html = ""
    if ep.get("resources") and not resources_main_html:
        links = "\n".join(f'              <a href="{r["url"]}">{r["title"]} &rarr;</a>' for r in ep["resources"])
        resources_html = f'''
          <div class="sidebar-card">
            <h3 class="sidebar-card__title">Resources</h3>
            <div class="sidebar-card__links">
{links}
            </div>
          </div>'''

    # Header image
    header_img = ep.get("image") or "never_again.jpg"
    header_alt = ep.get("image_alt", ep["title"])

    # SEO: episode-specific structured data
    iso_date = parse_episode_date(ep["date"]).strftime("%Y-%m-%d")
    ep_jsonld = {
        "@context": "https://schema.org",
        "@type": "PodcastEpisode",
        "name": ep["title"],
        "description": ep["description"],
        "url": f"{SITE_URL}/episode-{ep['slug']}.html",
        "datePublished": iso_date,
        "timeRequired": duration_to_iso(ep["duration"]),
        "episodeNumber": ep["number"],
        "image": f"{SITE_URL}/{ep.get('image', 'The_Melting_Pod_Podcast_Logo_3000.png')}",
        "partOfSeries": {
            "@type": "PodcastSeries",
            "name": "The Melting Pod",
            "url": f"{SITE_URL}/",
        },
    }
    if ep.get("megaphone_id"):
        ep_jsonld["associatedMedia"] = {
            "@type": "MediaObject",
            "contentUrl": f"https://player.megaphone.fm/{ep['megaphone_id']}",
        }
    if ep.get("guest"):
        ep_jsonld["actor"] = {"@type": "Person", "name": ep["guest"]["name"]}

    breadcrumb_jsonld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Episodes", "item": f"{SITE_URL}/episodes.html"},
            {"@type": "ListItem", "position": 3, "name": ep["title"]},
        ],
    }

    head = build_head(
        f'{ep["title"]} &mdash; The Melting Pod',
        smart_truncate(ep["description"]),
        page_url=f"episode-{ep['slug']}.html",
        og_image=ep.get("image", ""),
        og_type="article",
        published_date=iso_date,
        jsonld=[build_podcast_series_jsonld(), ep_jsonld, breadcrumb_jsonld],
    )
    nav = build_nav_html("episodes.html")
    footer = build_footer(include_newsletter=False)
    top_nav_html = build_episode_top_nav(prev_ep, next_ep)
    bottom_nav_html = build_episode_bottom_nav(prev_ep, next_ep)

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav}

  <main id="main">

  <!-- Page Header -->
  <header class="page-header page-header--has-img">
    <img src="{header_img}" alt="{header_alt}" class="page-header__img">
    <div class="page-header__overlay"></div>
    <div class="container" style="position: relative; z-index: 1;">
      {top_nav_html}
      <div class="episode-detail__meta">
        <span class="latest__date" style="color: var(--silver);">{ep['date']}</span>
        <span class="latest__duration" style="color: var(--silver);">{ep['duration']}</span>
      </div>
      <h1 class="page-header__title">{ep['title']}</h1>
    </div>
  </header>

  <!-- Episode Detail -->
  <section class="episode-detail">
    <div class="container">
      <div class="episode-detail__grid">
        <div class="episode-detail__main">
          <!-- Player -->
{player_html}

          <!-- Description -->
          {summary_html if summary_html else f'<div class="episode-detail__desc"><p>{ep["description"]}</p></div>'}

{chapters_html}
{resources_main_html}
{transcript_html}
        </div>

        <!-- Sidebar -->
        <aside class="episode-detail__sidebar">
          <div class="sidebar-card">
            <h3 class="sidebar-card__title">Hosts</h3>
            <div class="sidebar-card__hosts">
              <div class="sidebar-host">
                <img src="claire.jpg" alt="Claire Trickler-McNulty" class="sidebar-host__avatar">
                <div>
                  <div class="sidebar-host__name">Claire Trickler-McNulty</div>
                </div>
              </div>
              <div class="sidebar-host">
                <img src="amanda.jpg" alt="Amanda Baran" class="sidebar-host__avatar">
                <div>
                  <div class="sidebar-host__name">Amanda Baran</div>
                </div>
              </div>
              <div class="sidebar-host">
                <img src="doug.jpeg" alt="Doug Rand" class="sidebar-host__avatar">
                <div>
                  <div class="sidebar-host__name">Doug Rand</div>
                </div>
              </div>
            </div>
          </div>
{guest_html}
{resources_html}
          <div class="sidebar-card">
            <h3 class="sidebar-card__title">Listen On</h3>
            <div class="sidebar-card__links">
              <a href="#">Apple Podcasts &rarr;</a>
              <a href="#">Spotify &rarr;</a>
              <a href="https://www.youtube.com/@themeltingpod">YouTube &rarr;</a>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </section>
{bottom_nav_html}
  </main>

{footer}

  <script src="main7.js"></script>
</body>
</html>'''


def build_about_page():
    """Build the about page (static content, not driven by episodes.json)."""
    org_jsonld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "The Melting Pod",
        "url": f"{SITE_URL}/",
        "logo": f"{SITE_URL}/The_Melting_Pod_Podcast_Logo_3000.png",
        "sameAs": [
            "https://www.youtube.com/@themeltingpod",
            "https://bsky.app/profile/meltingpod.bsky.social",
            "https://www.instagram.com/meltingpodshow",
        ],
        "contactPoint": {
            "@type": "ContactPoint",
            "email": "hello@meltingpod.org",
            "contactType": "customer support",
        },
    }
    head = build_head(
        "About &mdash; The Melting Pod",
        "Meet the hosts of The Melting Pod: three former federal officials who served four presidents across two decades.",
        page_url="about.html",
        og_image="womens_march.jpg",
        jsonld=[build_podcast_series_jsonld(), org_jsonld],
    )
    nav = build_nav_html("about.html")
    footer = build_footer(include_newsletter=True)

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav}

  <main id="main">

  <!-- Page Header -->
  <header class="page-header page-header--has-img">
    <img src="womens_march.jpg" alt="Two women wearing American flag headscarves sharing a moment of solidarity at a march" class="page-header__img">
    <div class="page-header__overlay"></div>
    <div class="container" style="position: relative; z-index: 1;">
      <h1 class="page-header__title">About the Show</h1>
      <p class="page-header__desc">Two decades of experience. Four presidents. One deeply broken system.</p>
    </div>
  </header>

  <!-- Intro -->
  <section class="about-intro">
    <div class="container">
      <p class="about-intro__text">
        Immigration has become one of the top concerns of Americans across the political spectrum. Yet the U.S. immigration system is so complex, contradictory, and confounding that it&rsquo;s incredibly difficult to interpret the news. <em>The Melting Pod</em> offers something new: hosts and guests who not only understand the intricacies of our immigration system, but who have labored to improve it through senior roles inside the U.S. government and across civil society.
      </p>
    </div>
  </section>

  <!-- Hosts -->
  <section class="hosts-section">
    <div class="container">
      <div class="section-label">Your Hosts</div>
      <div class="hosts-grid">

        <div class="host-card scroll-reveal">
          <div class="host-card__photo host-card__photo--1"><img src="claire.jpg" alt="Claire Trickler-McNulty"></div>
          <div class="host-card__body">
            <h2 class="host-card__name">Claire Trickler-McNulty</h2>
            <p class="host-card__bio">Claire knows immigration enforcement and border issues inside and out. Literally&thinsp;&mdash;&thinsp;she&rsquo;s held senior roles at ICE and at a leading nonprofit defending kids against ICE. Her career has spanned the full arc of immigration enforcement policy, giving her a rare perspective that bridges government and advocacy.</p>
          </div>
        </div>

        <div class="host-card scroll-reveal">
          <div class="host-card__photo host-card__photo--2"><img src="amanda.jpg" alt="Amanda Baran"></div>
          <div class="host-card__body">
            <h2 class="host-card__name">Amanda Baran</h2>
            <p class="host-card__bio">Amanda worked her way up from serving as an asylum officer to running all policy within U.S. Citizenship and Immigration Services (USCIS), an agency with 20,000 employees. Her knowledge of humanitarian immigration programs&thinsp;&mdash;&thinsp;asylum, refugee resettlement, TPS, and more&thinsp;&mdash;&thinsp;is vast and hard-earned.</p>
          </div>
        </div>

        <div class="host-card scroll-reveal">
          <div class="host-card__photo host-card__photo--3"><img src="doug.jpeg" alt="Doug Rand"></div>
          <div class="host-card__body">
            <h2 class="host-card__name">Doug Rand</h2>
            <p class="host-card__bio">Doug focuses on the mechanics of the legal immigration system&thinsp;&mdash;&thinsp;employment-based visas, green cards, and U.S. citizenship. He started this work as a science fellow in the Obama White House, then as a startup founder, and most recently as a senior advisor at U.S. Citizenship and Immigration Services (USCIS).</p>
          </div>
        </div>

      </div>
    </div>
  </section>


  </main>

{footer}

  <script src="main7.js"></script>
</body>
</html>'''


def build_contact_page():
    """Build the contact page (static content)."""
    head = build_head(
        "Contact &mdash; The Melting Pod",
        "Get in touch with The Melting Pod. Media inquiries, story tips, and general questions welcome.",
        page_url="contact.html",
        og_image="ice_facility.jpg",
        jsonld=[build_podcast_series_jsonld()],
    )
    nav = build_nav_html("contact.html")
    footer = build_footer(include_newsletter=True)

    return f'''<!DOCTYPE html>
<html lang="en">
{head}
<body>
{nav}

  <main id="main">

  <!-- Page Header -->
  <header class="page-header page-header--has-img">
    <img src="ice_facility.jpg" alt="Exterior of a large immigration detention facility with security fencing" class="page-header__img">
    <div class="page-header__overlay"></div>
    <div class="container" style="position: relative; z-index: 1;">
      <h1 class="page-header__title">Get in Touch</h1>
      <p class="page-header__desc">Story ideas, media inquiries, and general questions&thinsp;&mdash;&thinsp;we&rsquo;d love to hear from you.</p>
    </div>
  </header>

  <!-- Contact -->
  <section class="contact-section">
    <div class="container">
      <div class="contact-channels">
        <div class="contact-channel scroll-reveal">
          <div class="contact-channel__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          </div>
          <div>
            <div class="contact-channel__label">Feedback &amp; Questions</div>
            <div class="contact-channel__value"><a href="mailto:hello@meltingpod.org">hello@meltingpod.org</a></div>
          </div>
        </div>
        <div class="contact-channel scroll-reveal">
          <div class="contact-channel__icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          </div>
          <div>
            <div class="contact-channel__label">Press &amp; Media</div>
            <div class="contact-channel__value"><a href="mailto:press@meltingpod.org">press@meltingpod.org</a></div>
          </div>
        </div>
      </div>
    </div>
  </section>

  </main>

{footer}

  <script src="main7.js"></script>
</body>
</html>'''


def build_sitemap(episodes):
    """Generate sitemap.xml."""
    urls = []
    static_pages = [
        ("index.html", "1.0", "weekly"),
        ("episodes.html", "0.9", "weekly"),
        ("about.html", "0.7", "monthly"),
        ("contact.html", "0.5", "yearly"),
    ]
    for page, priority, freq in static_pages:
        urls.append(f"""  <url>
    <loc>{SITE_URL}/{page}</loc>
    <priority>{priority}</priority>
    <changefreq>{freq}</changefreq>
  </url>""")

    for ep in episodes:
        iso_date = parse_episode_date(ep["date"]).strftime("%Y-%m-%d")
        urls.append(f"""  <url>
    <loc>{SITE_URL}/episode-{ep['slug']}.html</loc>
    <lastmod>{iso_date}</lastmod>
    <priority>0.8</priority>
    <changefreq>monthly</changefreq>
  </url>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""


def build_robots_txt():
    """Generate robots.txt."""
    return f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""


def build_rss_feed(episodes):
    """Generate feed.xml (blog-style RSS 2.0)."""
    items = []
    for ep in reversed(episodes):  # newest first
        pub_date = parse_episode_date(ep["date"]).strftime("%a, %d %b %Y 00:00:00 +0000")
        desc = ep["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        items.append(f"""    <item>
      <title>{ep['title']}</title>
      <link>{SITE_URL}/episode-{ep['slug']}.html</link>
      <guid isPermaLink="true">{SITE_URL}/episode-{ep['slug']}.html</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{desc}</description>
    </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Melting Pod</title>
    <link>{SITE_URL}/</link>
    <description>Stories about our dysfunctional immigration system and where we go from here.</description>
    <language>en-us</language>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{SITE_URL}/The_Melting_Pod_Podcast_Logo_1400.png</url>
      <title>The Melting Pod</title>
      <link>{SITE_URL}/</link>
    </image>
{chr(10).join(items)}
  </channel>
</rss>
"""


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {path.relative_to(ROOT)}")


def main():
    clean = "--clean" in sys.argv

    all_episodes = load_episodes()
    episodes = sorted(
        [ep for ep in all_episodes if ep.get("published", True)],
        key=lambda ep: ep["number"],
    )
    skipped = len(all_episodes) - len(episodes)
    msg = f"Loaded {len(episodes)} episodes from data/episodes.json"
    if skipped:
        msg += f" ({skipped} unpublished)"
    print(msg + "\n")

    if clean:
        # Remove old generated episode detail pages
        for f in ROOT.glob("episode-*.html"):
            f.unlink()
            print(f"  removed {f.name}")
        print()

    print("Building pages:")

    # Homepage
    write_file(ROOT / "index.html", build_index(episodes))

    # Episodes listing
    write_file(ROOT / "episodes.html", build_episodes_page(episodes))

    # Individual episode pages (with prev/next navigation)
    for i, ep in enumerate(episodes):
        prev_ep = episodes[i - 1] if i > 0 else None
        next_ep = episodes[i + 1] if i < len(episodes) - 1 else None
        write_file(ROOT / f"episode-{ep['slug']}.html", build_episode_detail(ep, prev_ep, next_ep))

    # About page
    write_file(ROOT / "about.html", build_about_page())

    # Contact page
    write_file(ROOT / "contact.html", build_contact_page())

    # SEO files
    write_file(ROOT / "sitemap.xml", build_sitemap(episodes))
    write_file(ROOT / "robots.txt", build_robots_txt())
    write_file(ROOT / "feed.xml", build_rss_feed(episodes))

    print(f"\nDone! Built {2 + len(episodes) + 2} pages + sitemap.xml, robots.txt, feed.xml.")
    print("\nTo add a new episode:")
    print("  1. Add an entry to data/episodes.json")
    print("  2. Run: python build.py")


if __name__ == "__main__":
    main()
