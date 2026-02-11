"""
Cyber Resilience Toolkit (CRT) — Streamlit Portal Home.

This module defines the home page for the CRT multi-page Streamlit application.
It introduces what the CRT is positioned to do, surfaces the core conceptual
framing, and points to the Structural Controls & Frameworks view as the initial
orientation point.

Detailed structural explanations live within the individual module pages
under the `pages/` directory.
"""

from __future__ import annotations

import os
from typing import Dict

import streamlit as st

from core.helpers import (  # pylint: disable=import-error
    load_markdown_file,
    get_named_paths,
)

from core.theme import inject_global_styles

inject_global_styles()


def _get_paths(current_file: str) -> Dict[str, str]:
    """
    Resolve key filesystem paths relative to the current file.

    Parameters
    ----------
    current_file : str
        Typically passed as __file__ from this module.

    Returns
    -------
    dict
        A dictionary containing important root-relative paths used for
        loading brand assets and documentation.
    """
    paths = get_named_paths(current_file)
    root_path = paths["level_up_0"]

    return {
        "root": root_path,
        "brand_logo": os.path.join(root_path, "brand", "blake_logo.png"),
        # Sidebar image (e.g., grouping / overview visual)
        "sidebar_image": os.path.join(root_path, "images", "grouping-image-crt.png"),
        # Main-page "start here" hero image
        "hero_image": os.path.join(root_path, "images", "start-here.png"),
        "about_support_md": os.path.join(root_path, "docs", "about_and_support.md"),
    }


# -------------------------------------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------------------------------------


def _render_sidebar(paths: Dict[str, str]) -> None:
    """
    Render a structured sidebar navigation using Streamlit's modern
    st.sidebar.page_link() API. Modules are grouped into:

    - Programmes & Outputs (modules that form defined artefacts/bundles)
    - Structural Lenses (modules that present structured views)
    - Reference & Integration (supporting catalogues and plumbing)
    """
    brand_logo = paths["brand_logo"]
    sidebar_image = paths["sidebar_image"]
    about_support_md = paths["about_support_md"]
    root_path = paths["root"]

    # Branding
    if os.path.isfile(brand_logo):
        st.logo(brand_logo)

    # Optional sidebar image
    if os.path.isfile(sidebar_image):
        st.sidebar.image(sidebar_image, width="stretch")

    # ---------------------------
    # Programmes & Outputs
    # ---------------------------
    st.sidebar.title("🎛 Programmes & Outputs")
    st.sidebar.caption(
        "Construct governance, architecture, resilience and scenario artefacts from "
        "structured CRT catalogues and bundles."
    )

    st.sidebar.page_link(
        "pages/02_programme_builder_export.py",
        label="Programme Builder & AI Export",
        icon="🎛",
    )

    st.sidebar.divider()

    # ---------------------------
    # Structural Lenses
    # ---------------------------
    st.sidebar.title("🔎 Structural Lenses")
    st.sidebar.caption(
        "Examine controls, data, architecture, identity and suppliers "
        "through structured, read-only views."
    )

    st.sidebar.page_link(
        "pages/01_structural_controls_frameworks.py",
        label="Structural Controls & Frameworks",
        icon="📂",
    )
    st.sidebar.page_link(
        "pages/03_data_classification_registry.py",
        label="Data Classification Registry",
        icon="🧮",
    )
    st.sidebar.page_link(
        "pages/04_attack_surface_mapper.py",
        label="Attack Surface Mapper",
        icon="🧩",
    )
    st.sidebar.page_link(
        "pages/05_identity_access_lens.py",
        label="Identity & Access Lens",
        icon="🔐",
    )
    st.sidebar.page_link(
        "pages/06_supply_chain_exposure_scanner.py",
        label="Supply-Chain Exposure Scanner",
        icon="🛰️",
    )
    st.sidebar.page_link(
        "pages/07_telemetry_signal_console.py",
        label="Telemetry & Signal Console",
        icon="📡",
    )

    st.sidebar.divider()

    # ---------------------------
    # Reference & Integration
    # ---------------------------
    st.sidebar.title("📚 Reference & Integration")
    st.sidebar.caption(
        "Review reference catalogues and integration utilities that underpin "
        "the CRT structural model."
    )

    st.sidebar.page_link(
        "pages/08_reference_data_trusted_sources.py",
        label="Reference Data & Trusted Sources",
        icon="📚",
    )
    st.sidebar.page_link(
        "pages/09_system_integrator_hub.py",
        label="System Integrator Hub",
        icon="🔄",
    )

    st.sidebar.divider()

    # --- About & Support ---
    with st.sidebar.expander("ℹ️ About & Support"):
        support_md = load_markdown_file(about_support_md)
        if support_md:
            st.markdown(support_md, unsafe_allow_html=True)
        else:
            st.warning("Support information not available.")

        st.caption("Reference documents bundled with this distribution:")

        pdf_path = os.path.join(root_path, "docs", "cyber-resilience-toolkit-index-controls-reference.pdf")
        if os.path.isfile(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "📚 CRT — Index & Controls Reference",
                    f.read(),
                    file_name="cyber-resilience-toolkit-index-controls-reference.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        else:
            st.info("Reference PDF not found in /docs.")
# -------------------------------------------------------------------------------------------------
# Main content helpers
# -------------------------------------------------------------------------------------------------

def _render_intro_block() -> None:
    """
    Render the high-level conceptual introduction to the CRT.
    """
    st.markdown("### Overview")
    st.write(
        """
The Cyber Resilience Toolkit presents a single structural model that brings
together governance intent, control design, architectural components,
supply-chain relationships and operational signals. Each module provides a
different vantage point on this model, so outputs and exports preserve
consistent, well-formed context.
        """
    )


def _render_scope_block() -> None:
    """
    Render the 'What the CRT brings into view' section.
    """
    st.markdown("### What the CRT Brings Into View")
    st.write(
        """
The CRT sets out key elements that shape a cyber-resilience environment:

- Governance intent expressed through policies, standards, expectations and exceptions.
- Controls, safeguards and rationale captured across CRT catalogues.
- Architectural patterns spanning systems, identity, data, suppliers and service dependencies.
- Telemetry, signals and behavioural context showing how environments operate over time.
- Requirements and obligations that influence design, oversight and review activity.

These components are presented within a uniform structure so they can be
examined, aligned and referenced across different workflows.
        """
    )


def _render_capabilities_block() -> None:
    """
    Render the 'What the CRT sets out' section, focused on programme uses
    and artefact-oriented work.
    """
    st.markdown("### What the CRT Sets Out")
    st.write(
        """
Using the underlying catalogues and structural relationships, the CRT produces
structured views and exportable bundles that support work such as:

- Structuring policies, standards, exceptions and governance artefacts anchored to controls, scope and requirements.
- Assembling third-party questionnaires, audit checklists and review narratives from catalogue mappings.
- Examining architecture views, identity flows and exposure surfaces across assets, services and suppliers.
- Compiling vendor exposure context from supply-chain and dependency catalogues.
- Surfacing telemetry sources and operational signals within a consistent descriptive framework.
- Packaging governance, architecture and risk bundles for downstream review or AI-assisted interpretation workflows.

Each module expresses the same structural model from a different vantage point,
so exported artefacts preserve lineage back to the CRT catalogues and maintain
context across documentation, internal templates, and analytical processes.

CRT is a structural environment for assembling context and artefacts — not an
assessment or compliance engine.
        """
    )


def _render_structure_block() -> None:
    """
    Render the 'How the environment holds together' section.
    """
    st.markdown("### How the Environment Holds Together")
    st.write(
        """
The CRT is organised around three principles:

1. **A shared structural model**
   Controls, governance elements, architectural components and telemetry are aligned
   within a consistent descriptive framework.

2. **Perspective without fragmentation**
   Modules present different views of the same underlying structure—governance,
   architecture, operations, supply-chain and resilience—without creating divergent
   interpretations.

3. **Context that can be carried forward**
   Selected material can be organised into structured bundles for review,
   collaboration or AI-assisted interpretation. Bundles preserve lineage to the CRT catalogues,
   providing clarity across downstream work.
        """
    )


def _render_start_here_block(paths: Dict[str, str]) -> None:
    """
    Render the 'Start here' section with the start-here image
    and a link to the Structural Controls & Frameworks page.
    """
    hero_image = paths["hero_image"]

    # st.markdown("### 📂 Start Here")

    if os.path.isfile(hero_image):
        st.image(hero_image, width=160)

    st.page_link(
        "pages/01_structural_controls_frameworks.py",
        label="Structural Controls & Frameworks",
        icon="📂",
    )


def _render_footer() -> None:
    """
    Render the standard footer caption for the CRT portal.
    """
    st.divider()
    st.caption(
        "© Blake Media Ltd. | Cyber Resilience Toolkit by Blake Wiltshire — "
        "All content is structural and conceptual; no configuration or assurance is provided."
    )


# -------------------------------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------------------------------


def main() -> None:
    """
    Entrypoint for the CRT Streamlit home page.

    This function configures the Streamlit page, resolves filesystem paths,
    and renders the main layout components.
    """
    st.set_page_config(
        page_title="Cyber Resilience Toolkit (CRT)",
        layout="wide",
    )

    paths = _get_paths(__file__)

    # Sidebar content
    _render_sidebar(paths)

    # Header
    st.title("Cyber Resilience Toolkit (CRT)")
    st.caption(
        "*A shared structural model for governance, architecture, and resilience context.*"
    )

    # Main content layout:
    # 1) Overview
    # 2) What the CRT brings into view
    # 3) What the CRT sets out
    # 4) How the environment holds together
    # 5) Getting started (Structural Controls & Frameworks)
    # 6) Footer
    st.divider()
    _render_intro_block()
    st.divider()
    _render_scope_block()
    st.divider()
    _render_capabilities_block()
    st.divider()
    _render_structure_block()
    st.divider()
    _render_start_here_block(paths)
    _render_footer()


if __name__ == "__main__":
    main()
