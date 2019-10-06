import torch.nn as nn


def set_fr_module(args):
    if args.fr_module_type == 'psnet':
        net = psnet(signal_dim=args.signal_dim, fr_size=args.fr_size, n_filters=args.fr_n_filters,
                    inner_dim=args.fr_inner_dim, n_layers=args.fr_n_layers, kernel_size=args.fr_kernel_size)
    elif args.fr_module_type == 'fr':
        assert args.fr_size == args.fr_inner_dim * args.fr_upsampling, \
            'The desired size of the frequency representation (fr_size) must be equal to inner_dim*upsampling'
        net = FR_module(signal_dim=args.signal_dim, n_filters=args.fr_n_filters,
                        inner_dim=args.fr_inner_dim, n_layers=args.fr_n_layers, upsampling=args.fr_upsampling,
                        kernel_size=args.fr_kernel_size, kernel_out=args.fr_kernel_out)
    elif args.fr_module_type == 'wo_multi':
        net = wo_multi(signal_dim=args.signal_dim, n_filters=args.fr_n_filters,
                       inner_dim=args.fr_inner_dim, n_layers=args.fr_n_layers, upsampling=args.fr_upsampling,
                       kernel_size=args.fr_kernel_size, kernel_out=args.fr_kernel_out)
    elif args.fr_module_type == 'wo_convtranspose':
        net = wo_convtranspose(signal_dim=args.signal_dim, fr_size=args.fr_size, n_filters=args.fr_n_filters,
                               inner_dim=args.fr_inner_dim, n_layers=args.fr_n_layers, kernel_size=args.fr_kernel_size)
    else:
        raise NotImplementedError('Frequency representation module type not implemented')
    if args.use_cuda:
        net.cuda()
    return net


def set_counter_module(args):
    assert args.fr_size % args.c_downsampling == 0, \
        'The downsampling factor (c_downsampling) does not divide the frequency representation size (fr_size)'
    if args.c_module_type == 'regression':
        net = Counter(n_output=1, n_layers=args.c_n_layers, n_filters=args.c_n_filters, kernel_size=args.c_kernel_size,
                      fr_size=args.fr_size, downsampling=args.c_downsampling, kernel_in=args.c_kernel_in)
    elif args.c_module_type == 'classification':
        net = Counter(n_output=args.max_num_freq, n_layers=args.c_n_layers, n_filters=args.c_n_filters)
    else:
        NotImplementedError('Counter module type not implemented')
    if args.use_cuda:
        net.cuda()
    return net


class psnet(nn.Module):
    def __init__(self, signal_dim=50, fr_size=1000, n_filters=8, inner_dim=100, n_layers=3, kernel_size=3):
        super().__init__()
        self.fr_size = fr_size
        self.num_filters = n_filters
        self.in_layer = nn.Linear(2 * signal_dim, inner_dim, bias=False)
        mod = []
        for n in range(n_layers):
            in_filters = n_filters if n > 0 else 1
            mod += [
                nn.Conv1d(in_channels=in_filters, out_channels=n_filters, kernel_size=kernel_size,
                          stride=1, padding=kernel_size // 2, bias=False),
                nn.BatchNorm1d(n_filters),
                nn.ReLU()
            ]
        self.mod = nn.Sequential(*mod)
        self.out_layer = nn.Linear(inner_dim * n_filters, fr_size, bias=True)

    def forward(self, inp):
        bsz = inp.size(0)
        inp = inp.view(bsz, -1)
        x = self.in_layer(inp).view(bsz, 1, -1)
        x = self.mod(x).view(bsz, -1)
        output = self.out_layer(x)
        return output


class FR_module(nn.Module):
    def __init__(self, signal_dim=50, n_filters=8, n_layers=3, inner_dim=125,
                 kernel_size=3, upsampling=8, kernel_out=25):
        super().__init__()
        self.fr_size = inner_dim * upsampling
        self.n_filters = n_filters
        self.in_layer = nn.Linear(2 * signal_dim, inner_dim * n_filters, bias=False)
        mod = []
        for n in range(n_layers):
            mod += [
                nn.Conv1d(n_filters, n_filters, kernel_size=kernel_size, padding=kernel_size - 1, bias=False,
                          padding_mode='circular'),
                nn.BatchNorm1d(n_filters),
                nn.ReLU(),
            ]
        self.mod = nn.Sequential(*mod)
        self.out_layer = nn.ConvTranspose1d(n_filters, 1, kernel_out, stride=upsampling,
                                            padding=(kernel_out - upsampling + 1) // 2, output_padding=1, bias=False)

    def forward(self, inp):
        bsz = inp.size(0)
        inp = inp.view(bsz, -1)
        x = self.in_layer(inp).view(bsz, self.n_filters, -1)
        x = self.mod(x)
        x = self.out_layer(x).view(bsz, -1)
        return x


class Counter(nn.Module):
    def __init__(self, n_output, n_layers, n_filters, kernel_size, fr_size, downsampling, kernel_in):
        super().__init__()
        counter = [nn.Conv1d(1, n_filters, kernel_in, stride=downsampling, padding=kernel_in - downsampling,
                             padding_mode='circular')]
        for i in range(n_layers):
            counter += [
                nn.Conv1d(n_filters, n_filters, kernel_size=kernel_size, padding=kernel_size - 1, bias=False,
                          padding_mode='circular'),
                nn.BatchNorm1d(n_filters),
                nn.ReLU(),
            ]
        counter += [nn.Conv1d(n_filters, 1, 1)]
        self.counter = nn.Sequential(*counter)
        self.out_layer = nn.Linear(fr_size // downsampling, n_output)

    def forward(self, inp):
        bsz = inp.size(0)
        inp = inp[:, None]
        x = self.counter(inp)
        x = x.view(bsz, -1)
        y = self.out_layer(x)
        return y


class wo_multi(nn.Module):
    def __init__(self, signal_dim=50, n_filters=8, n_layers=3, inner_dim=125,
                 kernel_size=3, upsampling=8, kernel_out=25):
        super().__init__()
        self.fr_size = inner_dim * upsampling
        self.num_filters = n_filters
        self.in_layer = nn.Linear(2 * signal_dim, inner_dim, bias=False)
        mod = []
        for n in range(n_layers):
            in_filters = n_filters if n > 0 else 1
            mod += [
                nn.Conv1d(in_channels=in_filters, out_channels=n_filters, kernel_size=kernel_size,
                          stride=1, padding=kernel_size // 2, bias=False),
                nn.BatchNorm1d(n_filters),
                nn.ReLU()
            ]
        self.mod = nn.Sequential(*mod)
        self.out_layer = nn.ConvTranspose1d(n_filters, 1, kernel_out, stride=upsampling,
                                            padding=(kernel_out - upsampling + 1) // 2, output_padding=1, bias=False)

    def forward(self, inp):
        bsz = inp.size(0)
        inp = inp.view(bsz, -1)
        x = self.in_layer(inp).view(bsz, 1, -1)
        x = self.mod(x)
        output = self.out_layer(x).view(bsz, -1)
        return output


class wo_convtranspose(nn.Module):
    def __init__(self, signal_dim=50, n_filters=8, n_layers=3, inner_dim=125, kernel_size=3, fr_size=1000):
        super().__init__()
        self.fr_size = fr_size
        self.n_filters = n_filters
        self.in_layer = nn.Linear(2 * signal_dim, n_filters * inner_dim, bias=False)
        mod = []
        for n in range(n_layers):
            mod += [
                nn.Conv1d(in_channels=n_filters, out_channels=n_filters, kernel_size=kernel_size,
                          stride=1, padding=kernel_size // 2, bias=False),
                nn.BatchNorm1d(n_filters),
                nn.ReLU()
            ]
        self.mod = nn.Sequential(*mod)
        self.out_layer = nn.Linear(inner_dim * n_filters, fr_size, bias=False)

    def forward(self, inp):
        bsz = inp.size(0)
        inp = inp.view(bsz, -1)
        x = self.in_layer(inp).view(bsz, self.n_filters, -1)
        x = self.mod(x).view(bsz, -1)
        output = self.out_layer(x)
        return output
