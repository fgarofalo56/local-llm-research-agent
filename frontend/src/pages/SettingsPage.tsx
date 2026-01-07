import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '@/api/client';
import { useTheme, THEMES, type ThemeVariant } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import {
  Save,
  RefreshCw,
  Check,
  X,
  Loader2,
  Sun,
  Moon,
  Monitor,
  Zap,
  Database,
  Settings2,
  ChevronDown,
  AlertCircle,
  Play,
  Palette,
  ChevronRight,
  Wrench,
  AlertTriangle,
} from 'lucide-react';
import type { HealthStatus } from '@/types';

// Official Ollama Logo SVG Component (llama face icon)
function OllamaLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={className} viewBox="294 159 1405 1857" fill="currentColor">
      <path d="M599.877 159.522C582.544 162.322 561.744 171.388 547.077 182.588C502.677 216.322 468.277 287.922 453.744 377.122C448.277 410.855 444.544 457.655 444.544 493.388C444.544 535.522 449.477 589.388 456.544 626.589C458.144 634.855 458.944 642.188 458.277 642.722C457.744 643.255 451.211 648.588 443.877 654.455C418.811 674.455 390.144 705.255 370.411 733.388C332.544 787.122 308.011 848.188 297.744 914.322C293.744 940.455 292.677 993.255 295.877 1019.39C302.944 1079.66 321.077 1130.59 352.144 1177.26L362.277 1192.32L359.344 1197.26C338.544 1232.19 320.811 1282.72 312.544 1331.26C306.011 1369.66 305.211 1379.92 305.211 1431.39C305.211 1483.26 305.877 1493.52 312.011 1529.39C319.344 1572.32 334.277 1617.79 350.944 1648.06C356.411 1657.92 369.744 1678.46 371.344 1679.52C371.877 1679.79 370.277 1684.72 367.744 1690.46C348.544 1732.46 332.144 1788.32 325.344 1835.39C320.544 1867.66 319.877 1878.06 319.877 1912.06C319.877 1955.39 322.277 1976.46 331.344 2010.99L332.677 2016.06H389.744H446.944L443.211 2008.99C420.144 1966.32 418.011 1887.12 437.877 1808.06C446.944 1771.52 457.211 1744.72 476.411 1707.79L487.877 1685.39V1671.66C487.877 1658.86 487.611 1657.39 483.477 1648.99C480.277 1642.59 476.011 1637.12 468.411 1629.66C455.477 1617.12 446.144 1603.92 438.677 1587.66C405.877 1516.46 399.477 1410.72 422.544 1320.59C432.144 1282.99 448.011 1249.52 464.677 1231.26C476.011 1218.72 481.877 1204.72 481.877 1190.19C481.877 1175.12 476.544 1162.72 464.544 1149.79C430.144 1112.99 408.944 1068.19 401.344 1016.06C390.544 941.788 410.144 860.855 454.677 796.722C498.277 733.788 559.477 693.388 627.877 682.589C643.211 680.055 671.877 680.455 687.877 683.388C705.344 686.455 716.277 685.522 727.477 680.188C741.344 673.655 748.277 665.522 756.411 646.855C763.611 630.188 769.211 621.122 784.277 602.322C802.411 579.788 819.877 564.455 847.877 545.922C879.877 524.988 916.277 509.788 952.544 502.455C965.744 499.788 971.877 499.388 996.544 499.388C1021.21 499.388 1027.34 499.788 1040.54 502.455C1093.74 513.255 1146.54 540.722 1188.68 579.655C1197.74 588.055 1219.48 614.988 1226.41 626.188C1229.08 630.588 1233.74 639.922 1236.68 646.855C1244.81 665.522 1251.74 673.655 1265.61 680.188C1276.41 685.388 1287.74 686.455 1304.54 683.655C1331.08 679.122 1351.48 679.522 1377.48 684.855C1466.01 702.722 1543.08 775.655 1577.21 873.388C1606.94 959.122 1598.54 1048.86 1554.28 1117.39C1546.81 1128.99 1539.34 1138.32 1528.54 1149.79C1505.21 1174.72 1505.21 1205.66 1528.41 1231.26C1566.54 1272.99 1590.41 1375.66 1583.21 1466.19C1578.41 1525.92 1563.08 1579.39 1542.01 1609.66C1538.28 1614.99 1530.54 1624.06 1524.68 1629.66C1517.08 1637.12 1512.81 1642.59 1509.61 1648.99C1505.48 1657.39 1505.21 1658.86 1505.21 1671.66V1685.39L1516.68 1707.79C1535.88 1744.72 1546.14 1771.52 1555.21 1808.06C1574.81 1886.06 1573.08 1963.66 1550.68 2007.79C1548.81 2011.52 1547.21 2014.99 1547.21 2015.39C1547.21 2015.79 1572.68 2016.06 1603.88 2016.06H1660.41L1661.88 2010.32C1662.68 2007.26 1664.01 2002.59 1664.68 1999.92C1666.14 1994.06 1669.08 1976.72 1671.48 1960.06C1673.74 1943.26 1673.74 1881.39 1671.48 1862.72C1662.94 1794.99 1648.68 1741.26 1625.34 1690.46C1622.81 1684.72 1621.21 1679.79 1621.74 1679.52C1622.41 1679.12 1626.14 1673.79 1630.14 1667.79C1659.21 1623.79 1677.08 1568.46 1686.14 1495.39C1688.54 1475.26 1688.54 1388.72 1686.14 1369.39C1679.74 1319.52 1672.01 1285.66 1659.21 1251.39C1653.88 1237.12 1639.74 1206.99 1633.74 1197.26L1630.81 1192.32L1640.94 1177.26C1672.01 1130.59 1690.14 1079.66 1697.21 1019.39C1700.41 993.255 1699.34 940.455 1695.34 914.322C1684.94 848.055 1660.54 787.255 1622.68 733.388C1602.94 705.255 1574.28 674.455 1549.21 654.455C1541.88 648.588 1535.34 643.255 1534.81 642.722C1534.14 642.188 1534.94 634.855 1536.54 626.589C1552.68 542.455 1552.14 437.522 1535.21 355.522C1520.54 284.055 1493.88 227.255 1459.48 194.455C1432.01 168.322 1404.01 157.122 1370.41 159.255C1293.34 163.788 1231.21 252.455 1206.68 392.188C1202.68 414.722 1199.21 441.122 1199.21 448.322C1199.21 451.122 1198.68 453.388 1198.01 453.388C1197.34 453.388 1192.14 450.722 1186.54 447.388C1127.08 412.188 1060.94 393.388 996.544 393.388C932.144 393.388 866.011 412.188 806.544 447.388C800.944 450.722 795.744 453.388 795.077 453.388C794.411 453.388 793.877 451.122 793.877 448.322C793.877 440.855 790.277 413.655 786.411 392.188C764.144 266.722 713.077 183.655 645.211 162.722C635.877 159.922 609.344 158.055 599.877 159.522ZM622.544 268.055C641.744 283.255 663.077 326.722 675.344 375.388C677.611 384.188 680.011 394.322 680.677 398.055C681.211 401.655 682.677 409.788 683.877 416.055C689.077 444.322 691.477 474.855 691.744 512.055L691.877 548.722L682.677 562.322L673.477 576.055H652.011C626.944 576.055 602.011 579.255 578.144 585.655C569.611 587.788 561.344 589.922 559.744 590.322C557.211 590.855 556.811 590.055 555.344 579.122C547.477 519.788 547.877 454.055 556.544 399.388C566.144 338.455 588.544 283.255 610.411 266.988C615.611 263.122 616.544 263.255 622.544 268.055ZM1382.81 267.122C1396.01 276.855 1410.54 302.722 1421.34 335.788C1443.08 401.922 1449.21 492.722 1437.74 579.122C1436.28 590.055 1435.88 590.855 1433.34 590.322C1431.74 589.922 1423.48 587.788 1414.94 585.655C1391.08 579.255 1366.14 576.055 1341.08 576.055H1319.61L1310.41 562.322L1301.21 548.722L1301.34 512.055C1301.61 460.322 1306.41 419.922 1317.88 374.988C1330.01 326.722 1351.48 283.255 1370.54 268.055C1376.54 263.255 1377.48 263.122 1382.81 267.122Z"/>
      <path d="M975.877 938.189C946.944 940.989 939.077 942.055 925.21 944.855C902.677 949.522 872.544 959.922 851.61 970.189C778.81 1005.79 728.677 1065.12 713.344 1133.79C710.277 1147.39 709.877 1151.92 709.877 1174.86C709.877 1197.52 710.277 1202.46 713.21 1215.39C733.61 1305.12 816.277 1371.39 923.21 1383.52C946.41 1386.06 1046.68 1386.06 1069.88 1383.52C1155.74 1373.79 1229.61 1327.26 1262.81 1261.92C1271.61 1244.46 1275.88 1233.12 1279.88 1215.39C1282.81 1202.46 1283.21 1197.52 1283.21 1174.86C1283.21 1151.92 1282.81 1147.39 1279.74 1133.79C1257.48 1034.06 1160.68 955.522 1042.01 940.589C1026.54 938.722 986.01 937.122 975.877 938.189ZM1025.74 1010.72C1065.34 1014.99 1105.21 1029.12 1137.21 1050.46C1154.41 1061.92 1178.68 1085.92 1189.08 1101.66C1201.88 1121.12 1209.21 1140.99 1212.54 1165.12C1214.01 1176.19 1213.21 1184.59 1209.21 1202.46C1202.94 1229.12 1183.48 1256.99 1157.21 1276.46C1144.94 1285.39 1119.48 1298.32 1103.88 1303.39C1074.28 1312.86 1054.94 1314.59 985.877 1314.06C940.81 1313.66 932.81 1313.26 919.877 1310.86C875.744 1302.59 840.81 1284.99 815.477 1258.19C794.944 1236.59 785.61 1216.86 780.544 1184.99C778.277 1170.19 782.544 1145.66 791.21 1124.99C801.744 1099.79 828.944 1068.46 855.877 1050.46C887.077 1029.66 928.144 1014.86 965.877 1010.86C980.41 1009.26 1011.21 1009.26 1025.74 1010.72Z"/>
      <path d="M945.61 1108.06C935.477 1113.52 928.41 1127.39 930.543 1137.66C932.943 1148.72 942.677 1159.92 957.877 1169.12C966.01 1174.06 966.543 1174.72 966.943 1179.66C967.21 1182.59 966.143 1190.99 964.677 1198.46C963.077 1205.79 961.877 1213.52 961.877 1215.66C962.01 1221.39 967.343 1230.72 972.943 1235.26C977.877 1239.26 978.81 1239.39 992.677 1239.79C1005.34 1240.19 1008.01 1239.92 1013.08 1237.52C1026.14 1231.12 1029.48 1219.39 1024.68 1196.86C1020.68 1178.06 1021.48 1175.12 1031.48 1169.39C1042.01 1163.26 1053.21 1152.46 1056.54 1145.12C1062.94 1131.12 1057.08 1115.26 1042.94 1107.92C1039.48 1106.19 1035.21 1105.39 1028.94 1105.39C1019.21 1105.39 1012.94 1107.66 1001.48 1114.99L994.943 1119.12L990.81 1116.59C973.877 1106.59 970.81 1105.39 960.543 1105.52C953.21 1105.52 949.21 1106.19 945.61 1108.06Z"/>
      <path d="M621.878 953.255C598.278 960.722 580.678 978.055 571.611 1002.72C567.211 1014.46 565.078 1032.99 566.945 1042.99C571.345 1066.86 590.945 1088.59 613.211 1094.59C641.211 1101.92 662.145 1097.12 680.678 1078.72C691.478 1068.19 697.345 1058.99 703.211 1044.06C707.478 1033.52 707.745 1031.66 707.745 1016.72L707.878 1000.72L702.278 989.255C693.345 971.122 677.211 957.655 658.545 952.722C648.011 950.055 631.078 950.189 621.878 953.255Z"/>
      <path d="M1334.01 952.855C1315.74 957.789 1299.48 971.389 1290.81 989.255L1285.21 1000.72L1285.34 1016.72C1285.34 1031.66 1285.61 1033.52 1289.88 1044.06C1295.74 1058.99 1301.61 1068.19 1312.41 1078.72C1330.94 1097.12 1351.88 1101.92 1379.88 1094.59C1396.01 1090.32 1412.14 1076.72 1419.88 1060.86C1426.54 1047.39 1428.14 1037.66 1426.01 1022.32C1421.08 987.255 1400.54 961.789 1370.01 952.855C1361.08 950.189 1343.74 950.189 1334.01 952.855Z"/>
    </svg>
  );
}

// Official Microsoft Azure Logo SVG Component (Azure icon for Foundry Local)
function FoundryLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="azure-grad-1" x1="-1032.172" x2="-1059.213" y1="145.312" y2="65.426" gradientTransform="matrix(1 0 0 -1 1075 158)" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#114a8b"/>
          <stop offset="1" stopColor="#0669bc"/>
        </linearGradient>
        <linearGradient id="azure-grad-2" x1="-1023.725" x2="-1029.98" y1="108.083" y2="105.968" gradientTransform="matrix(1 0 0 -1 1075 158)" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopOpacity=".3"/>
          <stop offset=".071" stopOpacity=".2"/>
          <stop offset=".321" stopOpacity=".1"/>
          <stop offset=".623" stopOpacity=".05"/>
          <stop offset="1" stopOpacity="0"/>
        </linearGradient>
        <linearGradient id="azure-grad-3" x1="-1027.165" x2="-997.482" y1="147.642" y2="68.561" gradientTransform="matrix(1 0 0 -1 1075 158)" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#3ccbf4"/>
          <stop offset="1" stopColor="#2892df"/>
        </linearGradient>
      </defs>
      <path fill="url(#azure-grad-1)" d="M33.338 6.544h26.038l-27.03 80.087a4.152 4.152 0 0 1-3.933 2.824H8.149a4.145 4.145 0 0 1-3.928-5.47L29.404 9.368a4.152 4.152 0 0 1 3.934-2.825z"/>
      <path fill="#0078d4" d="M71.175 60.261h-41.29a1.911 1.911 0 0 0-1.305 3.309l26.532 24.764a4.171 4.171 0 0 0 2.846 1.121h23.38z"/>
      <path fill="url(#azure-grad-2)" d="M33.338 6.544a4.118 4.118 0 0 0-3.943 2.879L4.252 83.917a4.14 4.14 0 0 0 3.908 5.538h20.787a4.443 4.443 0 0 0 3.41-2.9l5.014-14.777 17.91 16.705a4.237 4.237 0 0 0 2.666.972H81.24L71.024 60.261l-29.781.007L59.47 6.544z"/>
      <path fill="url(#azure-grad-3)" d="M66.595 9.364a4.145 4.145 0 0 0-3.928-2.82H33.648a4.146 4.146 0 0 1 3.928 2.82l25.184 74.62a4.146 4.146 0 0 1-3.928 5.472h29.02a4.146 4.146 0 0 0 3.927-5.472z"/>
    </svg>
  );
}

interface ProviderInfo {
  id: string;
  name: string;
  display_name: string;
  icon: string;
  available: boolean;
  error: string | null;
  version: string | null;
}

interface ModelInfo {
  name: string;
  size: string | null;
  modified_at: string | null;
  family: string | null;
  parameter_size: string | null;
  quantization_level: string | null;
  supports_tools: boolean;
  tool_warning: string | null;
}

interface ProviderModelsResponse {
  provider: string;
  models: ModelInfo[];
  error: string | null;
}

interface ConnectionTestResult {
  success: boolean;
  provider: string;
  model: string | null;
  message: string;
  latency_ms: number | null;
  version: string | null;
  error: string | null;
}

interface ProviderConfig {
  provider: string;
  model: string;
  embeddingModel: string;
  host: string;
}

// Theme color preview swatch
function ThemePreviewSwatch({ colors, isActive }: { colors: { bg: string; primary: string; accent: string }; isActive: boolean }) {
  return (
    <div
      className={`flex h-8 w-full overflow-hidden rounded-md border-2 ${isActive ? 'border-primary' : 'border-transparent'}`}
    >
      <div className="flex-1" style={{ backgroundColor: colors.bg }} />
      <div className="w-4" style={{ backgroundColor: colors.primary }} />
      <div className="w-2" style={{ backgroundColor: colors.accent }} />
    </div>
  );
}

// Theme selector component with mode and variant selection
function ThemeSelector() {
  const { mode, setMode, variant, setVariant, resolvedMode } = useTheme();

  const modes = [
    { id: 'light' as const, label: 'Light', icon: Sun },
    { id: 'dark' as const, label: 'Dark', icon: Moon },
    { id: 'system' as const, label: 'System', icon: Monitor },
  ];

  // Filter themes based on current resolved mode
  const availableThemes = THEMES.filter(t => t.supportedModes.includes(resolvedMode));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="h-5 w-5" />
          Theme
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Mode Selection */}
        <div>
          <h4 className="mb-3 text-sm font-medium text-muted-foreground">Mode</h4>
          <div className="flex gap-2">
            {modes.map((m) => {
              const Icon = m.icon;
              const isActive = mode === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`flex flex-1 flex-col items-center gap-2 rounded-lg border p-3 transition-colors ${
                    isActive
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border hover:border-primary/50 hover:bg-muted'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-xs font-medium">{m.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Theme Variant Selection */}
        <div>
          <h4 className="mb-3 flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <Palette className="h-4 w-4" />
            Color Theme
            <span className="ml-1 rounded bg-muted px-1.5 py-0.5 text-xs">
              {resolvedMode === 'dark' ? 'Dark' : 'Light'} themes
            </span>
          </h4>
          <div className="grid grid-cols-3 gap-3 md:grid-cols-5">
            {availableThemes.map((t) => {
              const isActive = variant === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setVariant(t.id as ThemeVariant)}
                  className={`flex flex-col items-center gap-2 rounded-lg border p-3 transition-all ${
                    isActive
                      ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                      : 'border-border hover:border-primary/50 hover:bg-muted/50'
                  }`}
                  title={t.description}
                >
                  <ThemePreviewSwatch colors={t.previewColors} isActive={isActive} />
                  <span className="text-xs font-medium">{t.name}</span>
                  {isActive && <Check className="h-3 w-3 text-primary" />}
                </button>
              );
            })}
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Some themes are only available in {resolvedMode === 'dark' ? 'dark' : 'light'} mode.
            Switch modes to see all available themes.
          </p>
        </div>

        <p className="text-sm text-muted-foreground">
          Theme preferences are saved and persist across sessions.
        </p>
      </CardContent>
    </Card>
  );
}

// Helper to get provider icon component
function ProviderIcon({ providerId, className = "h-5 w-5" }: { providerId: string; className?: string }) {
  if (providerId === 'ollama') {
    return <OllamaLogo className={className} />;
  }
  if (providerId === 'foundry_local') {
    return <FoundryLogo className={className} />;
  }
  return <span className="text-xl">🤖</span>;
}

// Provider selector with icons
function ProviderSelector({
  providers,
  selectedProvider,
  onSelect,
  isLoading,
}: {
  providers: ProviderInfo[];
  selectedProvider: string;
  onSelect: (provider: string) => void;
  isLoading: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const selected = providers.find((p) => p.id === selectedProvider);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex w-full items-center justify-between rounded-lg border bg-background px-4 py-3 text-left hover:bg-muted disabled:opacity-50"
      >
        <div className="flex items-center gap-3">
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <ProviderIcon providerId={selectedProvider} className="h-6 w-6" />
          )}
          <div>
            <p className="font-medium">{selected?.display_name || 'Select Provider'}</p>
            {selected && (
              <p className="text-sm text-muted-foreground">
                {selected.available ? (
                  <span className="flex items-center gap-1 text-green-500">
                    <Check className="h-3 w-3" /> Available
                    {selected.version && ` (v${selected.version})`}
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-500">
                    <X className="h-3 w-3" /> Unavailable
                  </span>
                )}
              </p>
            )}
          </div>
        </div>
        <ChevronDown className={`h-5 w-5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border bg-popover shadow-lg">
          {providers.map((provider) => (
            <button
              key={provider.id}
              onClick={() => {
                onSelect(provider.id);
                setIsOpen(false);
              }}
              className={`flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-muted ${
                provider.id === selectedProvider ? 'bg-muted' : ''
              }`}
            >
              <ProviderIcon providerId={provider.id} className="h-6 w-6" />
              <div className="flex-1">
                <p className="font-medium">{provider.display_name}</p>
                <p className="text-sm text-muted-foreground">
                  {provider.available ? (
                    <span className="text-green-500">
                      Available{provider.version && ` (v${provider.version})`}
                    </span>
                  ) : (
                    <span className="text-red-500">
                      {provider.error ? provider.error.slice(0, 50) : 'Unavailable'}
                    </span>
                  )}
                </p>
              </div>
              {provider.id === selectedProvider && <Check className="h-4 w-4 text-primary" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Model selector dropdown with tool support indicators
function ModelSelector({
  models,
  selectedModel,
  onSelect,
  isLoading,
  error,
  onRefresh,
  showOnlyToolCapable = false,
}: {
  models: ModelInfo[];
  selectedModel: string;
  onSelect: (model: string) => void;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  showOnlyToolCapable?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [filterToolCapable, setFilterToolCapable] = useState(showOnlyToolCapable);

  // Filter models based on tool capability if filter is enabled
  const displayModels = filterToolCapable
    ? models.filter(m => m.supports_tools)
    : models;

  const selected = models.find((m) => m.name === selectedModel);
  const toolCapableCount = models.filter(m => m.supports_tools).length;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">Model</label>
        <div className="flex items-center gap-2">
          {models.length > 0 && (
            <button
              onClick={() => setFilterToolCapable(!filterToolCapable)}
              className={`flex items-center gap-1 rounded px-2 py-1 text-xs transition-colors ${
                filterToolCapable
                  ? 'bg-green-500/20 text-green-600 dark:text-green-400'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
              title={filterToolCapable ? 'Showing only tool-capable models' : 'Show only tool-capable models'}
            >
              <Wrench className="h-3 w-3" />
              {toolCapableCount}/{models.length}
            </button>
          )}
          <Button variant="ghost" size="sm" onClick={onRefresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>
      <div className="relative">
        <button
          onClick={() => !error && setIsOpen(!isOpen)}
          disabled={isLoading || !!error}
          className="flex w-full items-center justify-between rounded-lg border bg-background px-4 py-3 text-left hover:bg-muted disabled:opacity-50"
        >
          <div className="flex-1">
            {isLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading models...
              </span>
            ) : error ? (
              <span className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-4 w-4" />
                {error.slice(0, 50)}
              </span>
            ) : selected ? (
              <div className="flex items-center gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{selected.name}</p>
                    {selected.supports_tools ? (
                      <span className="flex items-center gap-1 rounded bg-green-500/20 px-1.5 py-0.5 text-xs text-green-600 dark:text-green-400">
                        <Wrench className="h-3 w-3" />
                        Tools
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 rounded bg-yellow-500/20 px-1.5 py-0.5 text-xs text-yellow-600 dark:text-yellow-400" title={selected.tool_warning || 'Limited tool support'}>
                        <AlertTriangle className="h-3 w-3" />
                        No Tools
                      </span>
                    )}
                  </div>
                  {selected.size && (
                    <p className="text-sm text-muted-foreground">{selected.size}</p>
                  )}
                </div>
              </div>
            ) : (
              <span className="text-muted-foreground">Select a model</span>
            )}
          </div>
          <ChevronDown className={`h-5 w-5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && displayModels.length > 0 && (
          <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border bg-popover shadow-lg">
            {displayModels.map((model) => (
              <button
                key={model.name}
                onClick={() => {
                  onSelect(model.name);
                  setIsOpen(false);
                }}
                className={`flex w-full items-center justify-between px-4 py-2 text-left hover:bg-muted ${
                  model.name === selectedModel ? 'bg-muted' : ''
                }`}
                title={model.tool_warning || undefined}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{model.name}</p>
                    {model.supports_tools ? (
                      <span title="Supports MCP tools">
                        <Wrench className="h-3 w-3 text-green-500" />
                      </span>
                    ) : (
                      <span title={model.tool_warning || 'Limited tool support'}>
                        <AlertTriangle className="h-3 w-3 text-yellow-500" />
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {[model.size, model.family, model.parameter_size]
                      .filter(Boolean)
                      .join(' • ')}
                  </p>
                </div>
                {model.name === selectedModel && <Check className="h-4 w-4 text-primary" />}
              </button>
            ))}
          </div>
        )}

        {isOpen && displayModels.length === 0 && filterToolCapable && (
          <div className="absolute z-50 mt-1 w-full rounded-lg border bg-popover p-4 text-center text-sm text-muted-foreground shadow-lg">
            No tool-capable models available.
            <button
              onClick={() => setFilterToolCapable(false)}
              className="mt-2 block w-full text-primary hover:underline"
            >
              Show all models
            </button>
          </div>
        )}
      </div>

      {/* Show warning if selected model doesn't support tools */}
      {selected && !selected.supports_tools && selected.tool_warning && (
        <div className="flex items-start gap-2 rounded-lg bg-yellow-500/10 p-3 text-sm text-yellow-700 dark:text-yellow-400">
          <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <p>{selected.tool_warning}</p>
        </div>
      )}
    </div>
  );
}

// Connection test button
function ConnectionTestButton({
  provider,
  model,
}: {
  provider: string;
  model: string | null;
}) {
  const testMutation = useMutation({
    mutationFn: (data: { provider: string; model: string | null }) =>
      api.post<ConnectionTestResult>('/settings/providers/test', data),
  });

  const handleTest = () => {
    testMutation.mutate({ provider, model });
  };

  return (
    <div className="space-y-2">
      <Button
        onClick={handleTest}
        disabled={testMutation.isPending}
        variant={testMutation.data?.success ? 'default' : 'outline'}
        className="w-full"
      >
        {testMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Testing...
          </>
        ) : (
          <>
            <Zap className="mr-2 h-4 w-4" />
            Test Connection
          </>
        )}
      </Button>

      {testMutation.data && (
        <div
          className={`rounded-lg p-3 ${
            testMutation.data.success
              ? 'bg-green-500/10 text-green-700 dark:text-green-400'
              : 'bg-red-500/10 text-red-700 dark:text-red-400'
          }`}
        >
          <div className="flex items-center gap-2">
            {testMutation.data.success ? (
              <Check className="h-4 w-4" />
            ) : (
              <X className="h-4 w-4" />
            )}
            <span className="font-medium">{testMutation.data.message}</span>
          </div>
          {testMutation.data.latency_ms && (
            <p className="mt-1 text-sm">Response time: {testMutation.data.latency_ms}ms</p>
          )}
          {testMutation.data.error && (
            <p className="mt-1 text-sm">{testMutation.data.error}</p>
          )}
        </div>
      )}
    </div>
  );
}

// Service start response interfaces
interface ServiceStartResponse {
  success: boolean;
  message: string;
  endpoint: string | null;
  error: string | null;
  is_docker: boolean;
}

interface FoundryStartResponse extends ServiceStartResponse {
  model: string | null;
}

// Start Ollama button component
function StartOllamaButton({ onSuccess }: { onSuccess?: () => void }) {
  const startMutation = useMutation({
    mutationFn: () =>
      api.post<ServiceStartResponse>('/settings/providers/ollama/start', {}),
    onSuccess: (data) => {
      if (data.success && onSuccess) {
        onSuccess();
      }
    },
  });

  const handleStart = () => {
    startMutation.mutate();
  };

  return (
    <div className="space-y-2">
      <Button
        onClick={handleStart}
        disabled={startMutation.isPending}
        variant="outline"
        className="w-full"
      >
        {startMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Starting Ollama...
          </>
        ) : (
          <>
            <Play className="mr-2 h-4 w-4" />
            Start Ollama
          </>
        )}
      </Button>

      {startMutation.data && (
        <div
          className={`rounded-lg p-3 ${
            startMutation.data.success
              ? 'bg-green-500/10 text-green-700 dark:text-green-400'
              : startMutation.data.is_docker
                ? 'bg-blue-500/10 text-blue-700 dark:text-blue-400'
                : 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400'
          }`}
        >
          <div className="flex items-center gap-2">
            {startMutation.data.success ? (
              <Check className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <span className="font-medium">{startMutation.data.message}</span>
          </div>
          {startMutation.data.endpoint && (
            <p className="mt-1 text-sm">Endpoint: {startMutation.data.endpoint}</p>
          )}
          {startMutation.data.error && (
            <p className="mt-1 text-sm whitespace-pre-wrap">{startMutation.data.error}</p>
          )}
        </div>
      )}
    </div>
  );
}

// Foundry start button component
function StartFoundryButton({ model, onSuccess }: { model: string | null; onSuccess?: () => void }) {
  const startMutation = useMutation({
    mutationFn: (data: { model: string | null }) =>
      api.post<FoundryStartResponse>('/settings/providers/foundry/start', data),
    onSuccess: (data) => {
      if (data.success && onSuccess) {
        onSuccess();
      }
    },
  });

  const handleStart = () => {
    startMutation.mutate({ model });
  };

  return (
    <div className="space-y-2">
      <Button
        onClick={handleStart}
        disabled={startMutation.isPending}
        variant="outline"
        className="w-full"
      >
        {startMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Starting Foundry...
          </>
        ) : (
          <>
            <Play className="mr-2 h-4 w-4" />
            Start Foundry Local
          </>
        )}
      </Button>

      {startMutation.data && (
        <div
          className={`rounded-lg p-3 ${
            startMutation.data.success
              ? 'bg-green-500/10 text-green-700 dark:text-green-400'
              : startMutation.data.is_docker
                ? 'bg-blue-500/10 text-blue-700 dark:text-blue-400'
                : 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400'
          }`}
        >
          <div className="flex items-center gap-2">
            {startMutation.data.success ? (
              <Check className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <span className="font-medium">{startMutation.data.message}</span>
          </div>
          {startMutation.data.endpoint && (
            <p className="mt-1 text-sm">Endpoint: {startMutation.data.endpoint}</p>
          )}
          {startMutation.data.error && (
            <p className="mt-1 text-sm whitespace-pre-wrap">{startMutation.data.error}</p>
          )}
        </div>
      )}
    </div>
  );
}

// Helper to load settings from localStorage
function loadSavedSettings() {
  if (typeof window === 'undefined') return null;
  try {
    const saved = localStorage.getItem('llm-settings');
    if (saved) {
      return JSON.parse(saved);
    }
  } catch {
    // Ignore parse errors
  }
  return null;
}

const defaultProviderConfig: ProviderConfig = {
  provider: 'ollama',
  model: 'qwen3:30b',
  embeddingModel: 'nomic-embed-text',
  host: 'http://localhost:11434',
};

const defaultSecondaryConfig: ProviderConfig = {
  provider: 'foundry_local',
  model: '',
  embeddingModel: '',
  host: 'http://127.0.0.1:53760',
};

interface SqlSettings {
  host: string;
  database: string;
}

const defaultSqlSettings: SqlSettings = {
  host: 'localhost',
  database: 'ResearchAnalytics',
};

export function SettingsPage() {
  const navigate = useNavigate();
  // Theme is handled by ThemeContext

  // Provider configuration state - initialize from localStorage
  const [providerConfig, setProviderConfig] = useState<ProviderConfig>(() => {
    const saved = loadSavedSettings();
    return saved?.primary || defaultProviderConfig;
  });

  // Secondary provider config (for dual provider support)
  const [secondaryConfig, setSecondaryConfig] = useState<ProviderConfig>(() => {
    const saved = loadSavedSettings();
    return saved?.secondary || defaultSecondaryConfig;
  });

  // SQL Server settings
  const [sqlSettings, setSqlSettings] = useState<SqlSettings>(() => {
    const saved = loadSavedSettings();
    return saved?.sql || defaultSqlSettings;
  });

  // Fetch providers list
  const { data: providers = [], isLoading: providersLoading, refetch: refetchProviders } = useQuery({
    queryKey: ['providers'],
    queryFn: () => api.get<ProviderInfo[]>('/settings/providers'),
    staleTime: 10000, // 10 seconds - shorter for faster availability updates
    refetchOnWindowFocus: true,
  });

  // Fetch models for selected provider
  const { data: modelsData, isLoading: modelsLoading, refetch: refetchModels } = useQuery({
    queryKey: ['models', providerConfig.provider],
    queryFn: () =>
      api.get<ProviderModelsResponse>(`/settings/providers/${providerConfig.provider}/models`),
    enabled: !!providerConfig.provider,
    staleTime: 5000, // 5 seconds - shorter for responsiveness
    refetchOnWindowFocus: true,
  });

  // Fetch models for secondary provider
  const { data: secondaryModelsData, isLoading: secondaryModelsLoading, refetch: refetchSecondaryModels } = useQuery({
    queryKey: ['models', secondaryConfig.provider],
    queryFn: () =>
      api.get<ProviderModelsResponse>(`/settings/providers/${secondaryConfig.provider}/models`),
    enabled: !!secondaryConfig.provider && secondaryConfig.provider !== providerConfig.provider,
    staleTime: 5000, // 5 seconds
    refetchOnWindowFocus: true,
  });

  // Health status
  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/health'),
  });

  const statusColors = {
    healthy: 'bg-green-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-yellow-500',
  };


  // Save settings to localStorage
  const handleSave = () => {
    localStorage.setItem(
      'llm-settings',
      JSON.stringify({
        primary: providerConfig,
        secondary: secondaryConfig,
        sql: sqlSettings,
      })
    );
    // Show success notification
    alert('Settings saved successfully!');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Theme Settings */}
      <ThemeSelector />

      {/* System Health */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            System Health
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={() => refetchHealth()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {health?.services.map((service) => (
              <div key={service.name} className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${statusColors[service.status]}`} />
                <div>
                  <p className="font-medium capitalize">{service.name.replace('_', ' ')}</p>
                  {service.latency_ms && (
                    <p className="text-sm text-muted-foreground">{service.latency_ms}ms</p>
                  )}
                  {service.message && (
                    <p className="text-sm text-muted-foreground truncate max-w-[200px]">
                      {service.message}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Primary LLM Provider Configuration */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <ProviderIcon providerId={providerConfig.provider} className="h-6 w-6" />
            Primary LLM Provider
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              refetchProviders();
              refetchModels();
            }}
            title="Refresh provider status and models"
          >
            <RefreshCw className={`h-4 w-4 ${providersLoading || modelsLoading ? 'animate-spin' : ''}`} />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <ProviderSelector
            providers={providers}
            selectedProvider={providerConfig.provider}
            onSelect={(provider) => {
              setProviderConfig((prev) => ({ ...prev, provider, model: '' }));
            }}
            isLoading={providersLoading}
          />

          <ModelSelector
            models={modelsData?.models || []}
            selectedModel={providerConfig.model}
            onSelect={(model) => setProviderConfig((prev) => ({ ...prev, model }))}
            isLoading={modelsLoading}
            error={modelsData?.error || null}
            onRefresh={() => refetchModels()}
          />

          <div>
            <label className="mb-1 block text-sm font-medium">Host URL</label>
            <Input
              value={providerConfig.host}
              onChange={(e) => setProviderConfig((prev) => ({ ...prev, host: e.target.value }))}
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Embedding Model</label>
            <Input
              value={providerConfig.embeddingModel}
              onChange={(e) =>
                setProviderConfig((prev) => ({ ...prev, embeddingModel: e.target.value }))
              }
              placeholder="nomic-embed-text"
            />
          </div>

          <ConnectionTestButton
            provider={providerConfig.provider}
            model={providerConfig.model || null}
          />

          {/* Show Start Ollama button if Ollama is selected but not available */}
          {providerConfig.provider === 'ollama' && !providers.find(p => p.id === 'ollama')?.available && (
            <StartOllamaButton onSuccess={() => refetchProviders()} />
          )}

          {/* Show Start Foundry button if Foundry is selected but not available */}
          {providerConfig.provider === 'foundry_local' && !providers.find(p => p.id === 'foundry_local')?.available && (
            <StartFoundryButton model={providerConfig.model || null} onSuccess={() => refetchProviders()} />
          )}
        </CardContent>
      </Card>

      {/* Secondary LLM Provider Configuration (Dual Provider Support) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <ProviderIcon providerId={secondaryConfig.provider} className="h-6 w-6" />
            Secondary LLM Provider (Optional)
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              refetchProviders();
              refetchSecondaryModels();
            }}
            title="Refresh provider status and models"
          >
            <RefreshCw className={`h-4 w-4 ${providersLoading || secondaryModelsLoading ? 'animate-spin' : ''}`} />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Configure a secondary provider to switch between providers without re-entering
            configuration.
          </p>

          <ProviderSelector
            providers={providers.filter((p) => p.id !== providerConfig.provider)}
            selectedProvider={secondaryConfig.provider}
            onSelect={(provider) => {
              setSecondaryConfig((prev) => ({ ...prev, provider, model: '' }));
            }}
            isLoading={providersLoading}
          />

          {secondaryConfig.provider && (
            <>
              <ModelSelector
                models={secondaryModelsData?.models || []}
                selectedModel={secondaryConfig.model}
                onSelect={(model) => setSecondaryConfig((prev) => ({ ...prev, model }))}
                isLoading={secondaryModelsLoading}
                error={secondaryModelsData?.error || null}
                onRefresh={() => refetchSecondaryModels()}
              />

              <div>
                <label className="mb-1 block text-sm font-medium">Host URL</label>
                <Input
                  value={secondaryConfig.host}
                  onChange={(e) =>
                    setSecondaryConfig((prev) => ({ ...prev, host: e.target.value }))
                  }
                />
              </div>

              <ConnectionTestButton
                provider={secondaryConfig.provider}
                model={secondaryConfig.model || null}
              />

              {/* Show Start Ollama button if Ollama is selected but not available */}
              {secondaryConfig.provider === 'ollama' && !providers.find(p => p.id === 'ollama')?.available && (
                <StartOllamaButton onSuccess={() => refetchProviders()} />
              )}

              {/* Show Start Foundry button if Foundry is selected but not available */}
              {secondaryConfig.provider === 'foundry_local' && !providers.find(p => p.id === 'foundry_local')?.available && (
                <StartFoundryButton model={secondaryConfig.model || null} onSuccess={() => refetchProviders()} />
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* SQL Server Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            SQL Server Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Host</label>
            <Input
              value={sqlSettings.host}
              onChange={(e) => setSqlSettings((prev) => ({ ...prev, host: e.target.value }))}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Database Name</label>
            <Input
              value={sqlSettings.database}
              onChange={(e) => setSqlSettings((prev) => ({ ...prev, database: e.target.value }))}
            />
          </div>
        </CardContent>
      </Card>

      {/* Backend Database Settings Link */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Backend Database Settings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-muted-foreground">
            Configure connection to SQL Server 2025 backend database (LLM_BackEnd) for conversation history, document metadata, and native vector embeddings.
          </p>
          <Button
            onClick={() => navigate('/settings/database')}
            variant="outline"
            className="w-full"
          >
            <Settings2 className="mr-2 h-4 w-4" />
            Manage Backend Database
            <ChevronRight className="ml-auto h-4 w-4" />
          </Button>
        </CardContent>
      </Card>

      {/* Save Button */}
      <Button onClick={handleSave} className="w-full">
        <Save className="mr-2 h-4 w-4" />
        Save Settings
      </Button>
    </div>
  );
}
