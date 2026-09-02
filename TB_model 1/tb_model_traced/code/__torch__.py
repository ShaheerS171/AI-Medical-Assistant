class TBModel(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  backbone : __torch__.torchxrayvision.models.DenseNet
  meta_fc : __torch__.torch.nn.modules.container.___torch_mangle_423.Sequential
  head : __torch__.torch.nn.modules.container.___torch_mangle_428.Sequential
  def forward(self: __torch__.TBModel,
    img: Tensor,
    meta: Tensor) -> Tensor:
    head = self.head
    meta_fc = self.meta_fc
    backbone = self.backbone
    _0 = [(backbone).forward(img, ), (meta_fc).forward(meta, )]
    input = torch.cat(_0, 1)
    return (head).forward(input, )
