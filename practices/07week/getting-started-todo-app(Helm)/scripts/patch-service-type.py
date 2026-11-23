#!/usr/bin/env python3
"""Make the backend Service type and port configurable in the katenary-generated chart.

katenary v3 renders the Service without `spec.type` and hardcodes port 3000.
Run this after every `katenary convert -f` so that:
  - `backend.serviceType` in values defaults to LoadBalancer (can select ClusterIP / LoadBalancer / NodePort).
  - `backend.servicePort` in values defaults to 80 (standard HTTP), routing to targetPort 3000.

Idempotent: running it multiple times does not duplicate changes.
"""
import sys
from pathlib import Path

CHART = Path(sys.argv[1] if len(sys.argv) > 1 else
             "charts/getting-started-todo-app.local_kind")

SERVICE = CHART / "templates" / "backend" / "service.yaml"
VALUES = CHART / "values.yaml"

TYPE_LINE = '  type: {{ .Values.backend.serviceType | default "LoadBalancer" }}\n'


def patch_service() -> None:
    if not SERVICE.is_file():
        return
    text = SERVICE.read_text(encoding="utf-8")
    
    # 1. Patch type
    if "backend.serviceType" not in text:
        if "\nspec:\n" in text:
            text = text.replace("\nspec:\n", "\nspec:\n" + TYPE_LINE, 1)
            print(f"[ok]   patched serviceType in {SERVICE}")
        elif "\r\nspec:\r\n" in text:
            text = text.replace("\r\nspec:\r\n", "\r\nspec:\r\n" + TYPE_LINE, 1)
            print(f"[ok]   patched serviceType in {SERVICE}")
    elif 'default "ClusterIP"' in text:
        text = text.replace('default "ClusterIP"', 'default "LoadBalancer"')
        print(f"[ok]   switched default serviceType to LoadBalancer in {SERVICE}")

    # 2. Patch port to support default 80
    if "backend.servicePort" not in text:
        text = text.replace("    port: 3000\n    protocol: TCP\n    targetPort: 3000",
                            '    port: {{ .Values.backend.servicePort | default 80 }}\n    protocol: TCP\n    targetPort: 3000')
        text = text.replace("    port: 3000\r\n    protocol: TCP\r\n    targetPort: 3000",
                            '    port: {{ .Values.backend.servicePort | default 80 }}\r\n    protocol: TCP\r\n    targetPort: 3000')
        print(f"[ok]   patched servicePort in {SERVICE}")

    # Standardize port name to http if port-3000
    if "name: port-3000" in text:
        text = text.replace("name: port-3000", "name: http")
        print(f"[ok]   renamed port name to http in {SERVICE}")

    SERVICE.write_text(text, encoding="utf-8")


def patch_values() -> None:
    if not VALUES.is_file():
        return
    text = VALUES.read_text(encoding="utf-8")
    
    # 1. Add or fix serviceType
    if "\n  serviceType:" not in text and "\r\n  serviceType:" not in text:
        if "\nbackend:\n" in text:
            text = text.replace("\nbackend:\n", "\nbackend:\n  serviceType: LoadBalancer\n", 1)
            print(f"[ok]   added backend.serviceType to {VALUES}")
        elif "\r\nbackend:\r\n" in text:
            text = text.replace("\r\nbackend:\r\n", "\r\nbackend:\r\n  serviceType: LoadBalancer\r\n", 1)
            print(f"[ok]   added backend.serviceType to {VALUES}")
    else:
        text = text.replace("  serviceType: ClusterIP", "  serviceType: LoadBalancer")

    # 2. Add servicePort
    if "\n  servicePort:" not in text and "\r\n  servicePort:" not in text:
        if "  serviceType: LoadBalancer\n" in text:
            text = text.replace("  serviceType: LoadBalancer\n", "  serviceType: LoadBalancer\n  servicePort: 80\n", 1)
            print(f"[ok]   added backend.servicePort to {VALUES}")
        elif "  serviceType: LoadBalancer\r\n" in text:
            text = text.replace("  serviceType: LoadBalancer\r\n", "  serviceType: LoadBalancer\r\n  servicePort: 80\r\n", 1)
            print(f"[ok]   added backend.servicePort to {VALUES}")

    VALUES.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_service()
    patch_values()
