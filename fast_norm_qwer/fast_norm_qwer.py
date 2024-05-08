import pathlib
import torch
import torch.utils.cpp_extension


srcpath = pathlib.Path(__file__).parent.absolute()

fast_norm_qwer_cuda = torch.utils.cpp_extension.load(
    "fast_norm_qwer_cuda",
    sources=[srcpath / "fast_norm_qwer.cpp", srcpath / "fast_norm_qwer_cuda.cu"],
    extra_cuda_cflags=["-U__CUDA_NO_BFLOAT16_CONVERSIONS__", "-U__CUDA_NO_BFLOAT16_OPERATORS__", "-O2", "-fmad=false"],
    verbose=1,
)


class FastRMSNormQwerFunc(torch.autograd.Function):
    @staticmethod
    def forward(ctx, input, weight, eps):
        assert input.is_contiguous()
        assert weight.is_contiguous()
        output = fast_norm_qwer_cuda.rms_norm_fwd(input.view(-1, input.shape[-1]), weight, eps).view_as(input)
        ctx.save_for_backward(input, weight)
        ctx.eps = eps
        return output

    @staticmethod
    def backward(ctx, grad_output):
        assert grad_output.is_contiguous()
        input, weight = ctx.saved_tensors
        eps = ctx.eps
        grad_input, grad_weight = fast_norm_qwer_cuda.rms_norm_bwd(input.view(-1, input.shape[-1]), weight, grad_output.view(-1, grad_output.shape[-1]), eps)
        grad_input = grad_input.view_as(input)
        return grad_input, grad_weight, None


def fast_rms_norm_qwer(input, weight, eps):
    return FastRMSNormQwerFunc.apply(input, weight, eps)