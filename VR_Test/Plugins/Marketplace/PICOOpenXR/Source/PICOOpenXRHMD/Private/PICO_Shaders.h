// Copyright® 2015-2023 PICO Technology Co., Ltd. All rights reserved.
// This plugin incorporates portions of the Unreal® Engine. Unreal® is a trademark or registered trademark of Epic Games, Inc. in the United States of America and elsewhere.
// Unreal® Engine, Copyright 1998 – 2023, Epic Games, Inc. All rights reserved.
#pragma once

#include "CoreMinimal.h"
#include "RHI.h"
#include "RenderResource.h"
#include "ShaderParameters.h"
#include "Shader.h"
#include "GlobalShader.h"
#include "ShaderParameterUtils.h"
#include "RHIStaticStates.h"

class FDisplayMappingPixelShader : public FGlobalShader
{
	DECLARE_SHADER_TYPE(FDisplayMappingPixelShader, Global);
public:

	class FArraySource : SHADER_PERMUTATION_BOOL("DISPLAY_MAPPING_PS_FROM_ARRAY");
	class FLinearInput : SHADER_PERMUTATION_BOOL("DISPLAY_MAPPING_INPUT_IS_LINEAR");
	using FPermutationDomain = TShaderPermutationDomain<FArraySource, FLinearInput>;

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return true;
	}

	FDisplayMappingPixelShader(const ShaderMetaType::CompiledShaderInitializerType& Initializer) :
		FGlobalShader(Initializer)
	{
		OutputDevice.Bind(Initializer.ParameterMap, TEXT("OutputDevice"));
		OutputGamut.Bind(Initializer.ParameterMap, TEXT("OutputGamut"));
		SceneTexture.Bind(Initializer.ParameterMap, TEXT("SceneTexture"));
		SceneSampler.Bind(Initializer.ParameterMap, TEXT("SceneSampler"));
		TextureToOutputGamutMatrix.Bind(Initializer.ParameterMap, TEXT("TextureToOutputGamutMatrix"));
	}
	FDisplayMappingPixelShader() = default;

	static FMatrix44f GamutToXYZMatrix(EDisplayColorGamut ColorGamut)
	{
		static const FMatrix44f sRGB_2_XYZ_MAT(
                        FVector3f(0.4124564f, 0.3575761f, 0.1804375f),
                        FVector3f(0.2126729f, 0.7151522f, 0.0721750f),
                        FVector3f(0.0193339f, 0.1191920f, 0.9503041f),
			FVector3f(0, 0, 0)
		);

		static const FMatrix44f Rec2020_2_XYZ_MAT(
                        FVector3f(0.6369736f, 0.1446172f, 0.1688585f),
                        FVector3f(0.2627066f, 0.6779996f, 0.0592938f),
                        FVector3f(0.0000000f, 0.0280728f, 1.0608437f),
			FVector3f(0, 0, 0)
		);

		static const FMatrix44f P3D65_2_XYZ_MAT(
                        FVector3f(0.4865906f, 0.2656683f, 0.1981905f),
                        FVector3f(0.2289838f, 0.6917402f, 0.0792762f),
                        FVector3f(0.0000000f, 0.0451135f, 1.0438031f),
			FVector3f(0, 0, 0)
		);
		switch (ColorGamut)
		{
		case EDisplayColorGamut::sRGB_D65: return sRGB_2_XYZ_MAT;
		case EDisplayColorGamut::Rec2020_D65: return Rec2020_2_XYZ_MAT;
		case EDisplayColorGamut::DCIP3_D65: return P3D65_2_XYZ_MAT;
		default:
			checkNoEntry();
			return FMatrix44f::Identity;
		}

	}

	static FMatrix44f XYZToGamutMatrix(EDisplayColorGamut ColorGamut)
	{
		static const FMatrix44f XYZ_2_sRGB_MAT(
                        FVector3f(3.2409699419f, -1.5373831776f, -0.4986107603f),
                        FVector3f(-0.9692436363f, 1.8759675015f, 0.0415550574f),
                        FVector3f(0.0556300797f, -0.2039769589f, 1.0569715142f),
			FVector3f(0, 0, 0)
		);

		static const FMatrix44f XYZ_2_Rec2020_MAT(
                        FVector3f(1.7166084f, -0.3556621f, -0.2533601f),
                        FVector3f(-0.6666829f, 1.6164776f, 0.0157685f),
                        FVector3f(0.0176422f, -0.0427763f, 0.94222867f),
			FVector3f(0, 0, 0)
		);

		static const FMatrix44f XYZ_2_P3D65_MAT(
                        FVector3f(2.4933963f, -0.9313459f, -0.4026945f),
                        FVector3f(-0.8294868f, 1.7626597f, 0.0236246f),
                        FVector3f(0.0358507f, -0.0761827f, 0.9570140f),
			FVector3f(0, 0, 0)
		);

		switch (ColorGamut)
		{
		case EDisplayColorGamut::sRGB_D65: return XYZ_2_sRGB_MAT;
		case EDisplayColorGamut::Rec2020_D65: return XYZ_2_Rec2020_MAT;
		case EDisplayColorGamut::DCIP3_D65: return XYZ_2_P3D65_MAT;
		default:
			checkNoEntry();
			return FMatrix44f::Identity;
		}

	}

	void SetParameters(FRHIBatchedShaderParameters& BatchedParameters, EDisplayOutputFormat DisplayOutputFormat, EDisplayColorGamut DisplayColorGamut, EDisplayColorGamut TextureColorGamut, FRHITexture* SceneTextureRHI, bool bSameSize)
	{
		int32 OutputDeviceValue = (int32)DisplayOutputFormat;
		int32 OutputGamutValue = (int32)DisplayColorGamut;

		SetShaderValue(BatchedParameters, OutputDevice, OutputDeviceValue);
		SetShaderValue(BatchedParameters, OutputGamut, OutputGamutValue);

		const FMatrix44f TextureGamutMatrixToXYZ = GamutToXYZMatrix(TextureColorGamut);
		const FMatrix44f XYZToDisplayMatrix = XYZToGamutMatrix(DisplayColorGamut);
		// note: we use mul(m,v) instead of mul(v,m) in the shaders for color conversions which is why matrix multiplication is reversed compared to what we usually do
		const FMatrix44f CombinedMatrix = XYZToDisplayMatrix * TextureGamutMatrixToXYZ;

		SetShaderValue(BatchedParameters, TextureToOutputGamutMatrix, CombinedMatrix);

		if (bSameSize)
		{
			SetTextureParameter(BatchedParameters, SceneTexture, SceneSampler, TStaticSamplerState<SF_Point>::GetRHI(), SceneTextureRHI);
		}
		else
		{
			SetTextureParameter(BatchedParameters, SceneTexture, SceneSampler, TStaticSamplerState<SF_Bilinear>::GetRHI(), SceneTextureRHI);
		}
	}

	static const TCHAR* GetSourceFilename()
	{
		return TEXT("/Engine/Private/DisplayMappingPixelShader.usf");
	}

	static const TCHAR* GetFunctionName()
	{
		return TEXT("DisplayMappingPS");
	}

private:
	LAYOUT_FIELD(FShaderParameter, OutputDevice);
	LAYOUT_FIELD(FShaderParameter, OutputGamut);
	LAYOUT_FIELD(FShaderParameter, TextureToOutputGamutMatrix);
	LAYOUT_FIELD(FShaderResourceParameter, SceneTexture);
	LAYOUT_FIELD(FShaderResourceParameter, SceneSampler);
};
