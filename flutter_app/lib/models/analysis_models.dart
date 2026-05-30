class DashboardStats {
  final int totalAnalyses;
  final int fmdPositive;
  final int healthy;
  final int rejected;
  final double positivityRate;
  final List<DistrictCount> districtCounts;
  final List<RecentCase> recentCases;

  DashboardStats({required this.totalAnalyses, required this.fmdPositive, required this.healthy, required this.rejected, required this.positivityRate, required this.districtCounts, required this.recentCases});

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    return DashboardStats(
      totalAnalyses: json['total_analyses'] ?? 0,
      fmdPositive: json['fmd_positive'] ?? 0,
      healthy: json['healthy'] ?? 0,
      rejected: json['rejected'] ?? 0,
      positivityRate: (json['positivity_rate'] ?? 0).toDouble(),
      districtCounts: ((json['district_counts'] ?? []) as List).map((e) => DistrictCount.fromJson(e)).toList(),
      recentCases: ((json['recent_cases'] ?? []) as List).map((e) => RecentCase.fromJson(e)).toList(),
    );
  }
}

class DistrictCount {
  final String district;
  final int count;
  DistrictCount({required this.district, required this.count});
  factory DistrictCount.fromJson(Map<String, dynamic> json) => DistrictCount(district: json['district'] ?? 'Unknown', count: json['count'] ?? 0);
}

class RecentCase {
  final String farmName;
  final String district;
  final String prediction;
  final String severity;
  final String date;
  RecentCase({required this.farmName, required this.district, required this.prediction, required this.severity, required this.date});
  factory RecentCase.fromJson(Map<String, dynamic> json) => RecentCase(
    farmName: json['farm_name'] ?? 'Unknown Farm',
    district: json['district'] ?? 'Unknown',
    prediction: json['prediction'] ?? 'Unknown',
    severity: json['severity'] ?? 'N/A',
    date: json['date'] ?? '',
  );
}
