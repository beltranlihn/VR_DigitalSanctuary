// Copyright 2023 PICO Inc. All Rights Reserved.

using UnrealBuildTool;

public class PICOOpenXREditor : ModuleRules
{
    public PICOOpenXREditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PublicDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "CoreUObject"
            }
        );

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "ContentBrowser",
                "AssetRegistry",
                "AssetTools",
                "DesktopPlatform",
                "EditorFramework",
                "UnrealEd",
                "PICOOpenXRRuntimeSettings",
                "OpenXRHMD",
                "PICOOpenXRInput",
                "PICOOpenXRHandTracking",
                "Json",
                "SlateCore",
                "Slate",
                "Engine",
                "RenderCore",
                "ToolMenus"
            }
        );
    }
}
