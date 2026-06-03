#!/usr/local/autopkg/python
# -*- coding: utf-8 -*-

import os
from glob import glob

from AppKit import (
    NSBitmapImageFileTypePNG,
    NSBitmapImageRep,
    NSDeviceRGBColorSpace,
    NSGraphicsContext,
    NSMakeRect,
    NSWorkspace,
)
from autopkglib import ProcessorError
from autopkglib.DmgMounter import DmgMounter


class MunkiIconExtractor(DmgMounter):
    description = (
        "Extracts a rendered app icon from a .app, .dmg, or directory and writes "
        "a PNG into the Munki icons directory."
    )

    input_variables = {
        "pathname": {
            "required": True,
            "description": (
                "Path to a .app, a .dmg, a directory containing a .app, or a "
                ".dmg/path/inside form."
            ),
        },
        "NAME": {
            "required": False,
            "description": "Default basename for the output icon file.",
        },
        "app_name": {
            "required": False,
            "description": "App bundle name to find, with or without .app.",
        },
        "icon_name": {
            "required": False,
            "description": "Output icon filename, with or without .png.",
        },
        "MUNKI_REPO": {
            "required": False,
            "description": "Path to the Munki repo. Defaults to MUNKI_REPO/icons.",
        },
        "output_dir": {
            "required": False,
            "description": "Optional override for the output directory.",
        },
        "icon_size": {
            "required": False,
            "description": "Rendered icon size in pixels.",
            "default": 256,
        },
        "overwrite": {
            "required": False,
            "description": "Overwrite an existing icon if present.",
            "default": False,
        },
    }

    output_variables = {
        "icon_path": {
            "description": "Full path to the extracted icon PNG.",
        },
        "icon_filename": {
            "description": "Filename of the extracted icon PNG.",
        },
        "app_path": {
            "description": "Resolved app bundle path used for extraction.",
        },
    }

    def main(self):
        pathname = self.env["pathname"]
        icon_name = self._resolve_icon_name()
        output_dir = self._resolve_output_dir()
        icon_size = int(self.env.get("icon_size", 256))
        overwrite = self._as_bool(self.env.get("overwrite", False))

        if not os.path.exists(pathname) and not self._is_dmg_subpath(pathname):
            raise ProcessorError(f"Source path does not exist: {pathname}")

        icon_path = os.path.join(output_dir, icon_name)
        if os.path.exists(icon_path) and not overwrite:
            self.output(f"Icon already exists, leaving in place: {icon_path}")
            self.env["icon_path"] = icon_path
            self.env["icon_filename"] = icon_name
            return

        mounted_dmg = None
        try:
            app_path, mounted_dmg = self._resolve_app_path(pathname, self.env.get("app_name"))
            png_data = self._render_icon_png(app_path, icon_size)
            if png_data is None:
                raise ProcessorError(f"Could not extract icon from app: {app_path}")

            os.makedirs(output_dir, exist_ok=True)
            with open(icon_path, "wb") as file_handle:
                file_handle.write(png_data)

            self.output(f"Wrote icon: {icon_path}")
            self.env["icon_path"] = icon_path
            self.env["icon_filename"] = icon_name
            self.env["app_path"] = app_path
        finally:
            if mounted_dmg:
                self.unmount(mounted_dmg)

    def _resolve_output_dir(self):
        output_dir = self.env.get("output_dir")
        if output_dir:
            return output_dir

        munki_repo = self.env.get("MUNKI_REPO")
        if munki_repo:
            return os.path.join(munki_repo, "icons")

        recipe_cache_dir = self.env.get("RECIPE_CACHE_DIR")
        if recipe_cache_dir:
            return recipe_cache_dir

        raise ProcessorError(
            "No output directory available. Set output_dir, MUNKI_REPO, or RECIPE_CACHE_DIR."
        )

    def _resolve_icon_name(self):
        icon_name = self.env.get("icon_name") or self.env.get("NAME")

        if not icon_name:
            app_name = self.env.get("app_name")
            if app_name:
                icon_name = os.path.splitext(app_name)[0]

        if not icon_name:
            raise ProcessorError("Could not determine icon_name. Set icon_name, NAME, or app_name.")

        if not icon_name.lower().endswith(".png"):
            icon_name = f"{icon_name}.png"

        return icon_name

    def _resolve_app_path(self, pathname, app_name):
        if pathname.lower().endswith(".app"):
            if not os.path.isdir(pathname):
                raise ProcessorError(f"App bundle not found: {pathname}")
            return pathname, None

        dmg_path, dmg, dmg_source_path = self.parsePathForDMG(pathname)
        if dmg:
            mount_point = self.mount(dmg_path)
            matches = glob(os.path.join(mount_point, dmg_source_path))
            if not matches:
                raise ProcessorError(f"No valid path found in disk image: {pathname}")
            if len(matches) > 1:
                raise ProcessorError(
                    f"Multiple source paths found in disk image path '{pathname}': {', '.join(matches)}"
                )

            resolved = matches[0]
            if resolved.lower().endswith(".app"):
                return resolved, dmg_path
            if os.path.isdir(resolved):
                return self._find_app(resolved, app_name), dmg_path
            raise ProcessorError(f"Resolved path is not an app or directory: {resolved}")

        if pathname.lower().endswith(".dmg"):
            mount_point = self.mount(pathname)
            return self._find_app(mount_point, app_name), pathname

        if os.path.isdir(pathname):
            return self._find_app(pathname, app_name), None

        raise ProcessorError(f"Unsupported source type: {pathname}")

    def _find_app(self, root_path, app_name=None):
        bundle_name = None
        if app_name:
            bundle_name = app_name if app_name.endswith(".app") else f"{app_name}.app"

        matches = []
        for dirpath, dirnames, _ in os.walk(root_path, topdown=True, followlinks=False):
            app_dirs = [dirname for dirname in dirnames if dirname.endswith(".app")]
            for dirname in app_dirs:
                if bundle_name is None or dirname == bundle_name:
                    matches.append(os.path.join(dirpath, dirname))
            dirnames[:] = [dirname for dirname in dirnames if not dirname.endswith(".app")]

        if not matches:
            if bundle_name:
                raise ProcessorError(f"Could not find app bundle '{bundle_name}' in: {root_path}")
            raise ProcessorError(f"Could not find a .app bundle in: {root_path}")

        if len(matches) > 1:
            raise ProcessorError(
                "Multiple .app bundles found. Set app_name to disambiguate: "
                + ", ".join(sorted(matches))
            )

        return matches[0]

    def _render_icon_png(self, app_path, size):
        image = NSWorkspace.sharedWorkspace().iconForFile_(app_path)
        if image is None:
            return None

        image.setTemplate_(False)
        image.setSize_((float(size), float(size)))

        bitmap = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None,
            int(size),
            int(size),
            8,
            4,
            True,
            False,
            NSDeviceRGBColorSpace,
            0,
            0,
        )
        if bitmap is None:
            return None

        context = NSGraphicsContext.graphicsContextWithBitmapImageRep_(bitmap)
        if context is None:
            return None

        NSGraphicsContext.saveGraphicsState()
        try:
            NSGraphicsContext.setCurrentContext_(context)
            image.drawInRect_(NSMakeRect(0.0, 0.0, float(size), float(size)))
        finally:
            NSGraphicsContext.restoreGraphicsState()

        png_data = bitmap.representationUsingType_properties_(NSBitmapImageFileTypePNG, {})
        if png_data is None:
            return None

        return bytes(png_data)

    @staticmethod
    def _is_dmg_subpath(pathname):
        for extension in DmgMounter.DMG_EXTENSIONS:
            if extension + "/" in pathname:
                return True
        return False

    @staticmethod
    def _as_bool(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() not in {"false", "no", "0", ""}


if __name__ == "__main__":
    PROCESSOR = MunkiIconExtractor()
    PROCESSOR.execute_shell()
