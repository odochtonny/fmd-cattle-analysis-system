import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../models/analysis_models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/professional_shell.dart';
import '../widgets/stat_card.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<DashboardStats> futureStats;

  @override
  void initState() {
    super.initState();
    futureStats = ApiService.fetchDashboardStats();
  }

  @override
  Widget build(BuildContext context) {
    return ProfessionalShell(
      title: 'Professional FMD Surveillance Dashboard',
      actions: [
        FilledButton.icon(
          onPressed: () => Navigator.pushNamed(context, '/analysis'),
          icon: const Icon(Icons.add_a_photo_outlined),
          label: const Text('New Analysis'),
        )
      ],
      child: FutureBuilder<DashboardStats>(
        future: futureStats,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final stats = snapshot.data ?? DashboardStats(totalAnalyses: 0, fmdPositive: 0, healthy: 0, rejected: 0, positivityRate: 0, districtCounts: [], recentCases: []);
          return RefreshIndicator(
            onRefresh: () async => setState(() => futureStats = ApiService.fetchDashboardStats()),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(24),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _heroBanner(context),
                const SizedBox(height: 20),
                LayoutBuilder(builder: (context, c) {
                  final columns = c.maxWidth > 1100 ? 4 : c.maxWidth > 700 ? 2 : 1;
                  return GridView.count(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisCount: columns,
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                    childAspectRatio: 1.65,
                    children: [
                      StatCard(title: 'Total Analyses', value: '${stats.totalAnalyses}', subtitle: 'All submitted cattle cases', icon: Icons.analytics_outlined, color: AppTheme.secondary),
                      StatCard(title: 'FMD Positive', value: '${stats.fmdPositive}', subtitle: 'Cases requiring attention', icon: Icons.coronavirus_outlined, color: AppTheme.danger),
                      StatCard(title: 'Healthy', value: '${stats.healthy}', subtitle: 'Low-risk cattle records', icon: Icons.verified_outlined, color: AppTheme.success),
                      StatCard(title: 'Positivity Rate', value: '${stats.positivityRate.toStringAsFixed(1)}%', subtitle: 'FMD positive over valid cases', icon: Icons.trending_up, color: AppTheme.warning),
                    ],
                  );
                }),
                const SizedBox(height: 20),
                LayoutBuilder(builder: (context, c) {
                  final wide = c.maxWidth > 900;
                  return wide
                      ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Expanded(flex: 6, child: _districtChart(stats)),
                          const SizedBox(width: 16),
                          Expanded(flex: 5, child: _riskPanel(stats)),
                        ])
                      : Column(children: [_districtChart(stats), const SizedBox(height: 16), _riskPanel(stats)]);
                }),
                const SizedBox(height: 20),
                _recentCases(stats),
              ]),
            ),
          );
        },
      ),
    );
  }

  Widget _heroBanner(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(colors: [Color(0xFF0F766E), Color(0xFF2563EB)]),
      ),
      child: Row(children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('AI-powered cattle FMD detection and outbreak intelligence', style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.white, fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            const Text('Mandatory farm identity, district, symptoms, cattle validation, image analysis, Random Forest decision fusion, and MongoDB evidence storage.', style: TextStyle(color: Colors.white70, height: 1.4)),
          ]),
        ),
        const SizedBox(width: 20),
        const Icon(Icons.monitor_heart_outlined, color: Colors.white, size: 72),
      ]),
    );
  }

  Widget _districtChart(DashboardStats stats) {
    final items = stats.districtCounts.take(6).toList();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('District FMD Case Distribution', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 12),
          SizedBox(
            height: 260,
            child: items.isEmpty
                ? const Center(child: Text('No district data yet'))
                : BarChart(BarChartData(
                    gridData: const FlGridData(show: false),
                    borderData: FlBorderData(show: false),
                    titlesData: FlTitlesData(
                      leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 32)),
                      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (value, meta) {
                        final i = value.toInt();
                        if (i < 0 || i >= items.length) return const SizedBox.shrink();
                        return Padding(padding: const EdgeInsets.only(top: 8), child: Text(items[i].district, style: const TextStyle(fontSize: 10)));
                      })),
                    ),
                    barGroups: [for (int i = 0; i < items.length; i++) BarChartGroupData(x: i, barRods: [BarChartRodData(toY: items[i].count.toDouble(), borderRadius: BorderRadius.circular(8))])],
                  )),
          ),
        ]),
      ),
    );
  }

  Widget _riskPanel(DashboardStats stats) {
    final valid = (stats.fmdPositive + stats.healthy).clamp(1, 999999);
    final fmdFraction = stats.fmdPositive / valid;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Risk Intelligence', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 16),
          SizedBox(height: 170, child: PieChart(PieChartData(sectionsSpace: 3, centerSpaceRadius: 45, sections: [
            PieChartSectionData(value: stats.fmdPositive.toDouble(), title: 'FMD', radius: 54),
            PieChartSectionData(value: stats.healthy.toDouble(), title: 'Healthy', radius: 54),
            PieChartSectionData(value: stats.rejected.toDouble(), title: 'Rejected', radius: 54),
          ]))),
          const SizedBox(height: 16),
          LinearProgressIndicator(value: fmdFraction, minHeight: 12, borderRadius: BorderRadius.circular(20)),
          const SizedBox(height: 8),
          Text('Current outbreak signal: ${(fmdFraction * 100).toStringAsFixed(1)}% of valid records are FMD-positive.'),
        ]),
      ),
    );
  }

  Widget _recentCases(DashboardStats stats) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Recent Analyses', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 12),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(columns: const [
              DataColumn(label: Text('Farm')),
              DataColumn(label: Text('District')),
              DataColumn(label: Text('Prediction')),
              DataColumn(label: Text('Severity')),
              DataColumn(label: Text('Date')),
            ], rows: stats.recentCases.map((e) => DataRow(cells: [
              DataCell(Text(e.farmName)),
              DataCell(Text(e.district)),
              DataCell(Text(e.prediction)),
              DataCell(Text(e.severity)),
              DataCell(Text(e.date)),
            ])).toList()),
          ),
        ]),
      ),
    );
  }
}
