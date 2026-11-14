// Copyright PICO Technology Co., Ltd. All rights reserved.
// This plugin incorporates portions of the Unreal® Engine. Unreal® is a trademark or registered trademark of Epic Games, Inc. in the United States of America and elsewhere.
// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.IO;

public class PICOOpenXRMR : ModuleRules
{
    public PICOOpenXRMR(ReadOnlyTargetRules Target) : base(Target)
    {
	    PublicDependencyModuleNames.AddRange(new string[]
	    {
		    "ProceduralMeshComponent",
	    });
	    
        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                    "Core",
                    "CoreUObject",
                    "Engine",
                    "HeadMountedDisplay",
                    "OpenXRHMD",
                    "RHI",
                    "RenderCore",
                    "PICOOpenXRLoader",
                    "PICOOpenXRRuntimeSettings",
                    "JsonUtilities",
                    "Json"
            }
            );
    }
}