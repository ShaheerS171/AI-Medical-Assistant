class _DenseBlock(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  denselayer1 : __torch__.torchxrayvision.models.___torch_mangle_140._DenseLayer
  denselayer2 : __torch__.torchxrayvision.models.___torch_mangle_147._DenseLayer
  denselayer3 : __torch__.torchxrayvision.models.___torch_mangle_154._DenseLayer
  denselayer4 : __torch__.torchxrayvision.models.___torch_mangle_161._DenseLayer
  denselayer5 : __torch__.torchxrayvision.models.___torch_mangle_168._DenseLayer
  denselayer6 : __torch__.torchxrayvision.models.___torch_mangle_175._DenseLayer
  denselayer7 : __torch__.torchxrayvision.models.___torch_mangle_182._DenseLayer
  denselayer8 : __torch__.torchxrayvision.models.___torch_mangle_189._DenseLayer
  denselayer9 : __torch__.torchxrayvision.models.___torch_mangle_196._DenseLayer
  denselayer10 : __torch__.torchxrayvision.models.___torch_mangle_203._DenseLayer
  denselayer11 : __torch__.torchxrayvision.models.___torch_mangle_210._DenseLayer
  denselayer12 : __torch__.torchxrayvision.models.___torch_mangle_217._DenseLayer
  denselayer13 : __torch__.torchxrayvision.models.___torch_mangle_224._DenseLayer
  denselayer14 : __torch__.torchxrayvision.models.___torch_mangle_231._DenseLayer
  denselayer15 : __torch__.torchxrayvision.models.___torch_mangle_238._DenseLayer
  denselayer16 : __torch__.torchxrayvision.models.___torch_mangle_245._DenseLayer
  denselayer17 : __torch__.torchxrayvision.models.___torch_mangle_252._DenseLayer
  denselayer18 : __torch__.torchxrayvision.models.___torch_mangle_259._DenseLayer
  denselayer19 : __torch__.torchxrayvision.models.___torch_mangle_266._DenseLayer
  denselayer20 : __torch__.torchxrayvision.models.___torch_mangle_273._DenseLayer
  denselayer21 : __torch__.torchxrayvision.models.___torch_mangle_280._DenseLayer
  denselayer22 : __torch__.torchxrayvision.models.___torch_mangle_287._DenseLayer
  denselayer23 : __torch__.torchxrayvision.models.___torch_mangle_294._DenseLayer
  denselayer24 : __torch__.torchxrayvision.models.___torch_mangle_301._DenseLayer
  def forward(self: __torch__.torchxrayvision.models.___torch_mangle_302._DenseBlock,
    argument_1: Tensor) -> Tensor:
    denselayer24 = self.denselayer24
    denselayer23 = self.denselayer23
    denselayer22 = self.denselayer22
    denselayer21 = self.denselayer21
    denselayer20 = self.denselayer20
    denselayer19 = self.denselayer19
    denselayer18 = self.denselayer18
    denselayer17 = self.denselayer17
    denselayer16 = self.denselayer16
    denselayer15 = self.denselayer15
    denselayer14 = self.denselayer14
    denselayer13 = self.denselayer13
    denselayer12 = self.denselayer12
    denselayer11 = self.denselayer11
    denselayer10 = self.denselayer10
    denselayer9 = self.denselayer9
    denselayer8 = self.denselayer8
    denselayer7 = self.denselayer7
    denselayer6 = self.denselayer6
    denselayer5 = self.denselayer5
    denselayer4 = self.denselayer4
    denselayer3 = self.denselayer3
    denselayer2 = self.denselayer2
    denselayer1 = self.denselayer1
    _0 = (denselayer2).forward((denselayer1).forward(argument_1, ), )
    _1 = (denselayer4).forward((denselayer3).forward(_0, ), )
    _2 = (denselayer6).forward((denselayer5).forward(_1, ), )
    _3 = (denselayer8).forward((denselayer7).forward(_2, ), )
    _4 = (denselayer10).forward((denselayer9).forward(_3, ), )
    _5 = (denselayer12).forward((denselayer11).forward(_4, ), )
    _6 = (denselayer14).forward((denselayer13).forward(_5, ), )
    _7 = (denselayer16).forward((denselayer15).forward(_6, ), )
    _8 = (denselayer18).forward((denselayer17).forward(_7, ), )
    _9 = (denselayer20).forward((denselayer19).forward(_8, ), )
    _10 = (denselayer22).forward((denselayer21).forward(_9, ), )
    _11 = (denselayer24).forward((denselayer23).forward(_10, ), )
    return _11
