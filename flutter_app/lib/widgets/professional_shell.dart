import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class ProfessionalShell extends StatelessWidget {
  final String title;
  final Widget child;
  final List<Widget>? actions;

  const ProfessionalShell({super.key, required this.title, required this.child, this.actions});

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final isWide = width >= 900;

    return Scaffold(
      body: Row(
        children: [
          if (isWide) const _SideNav(),
          Expanded(
            child: Column(
              children: [
                Container(
                  height: 72,
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  decoration: const BoxDecoration(color: Colors.white),
                  child: Row(
                    children: [
                      if (!isWide)
                        Builder(builder: (context) => IconButton(icon: const Icon(Icons.menu), onPressed: () => Scaffold.of(context).openDrawer())),
                      Text(title, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                      const Spacer(),
                      ...?actions,
                    ],
                  ),
                ),
                Expanded(child: child),
              ],
            ),
          ),
        ],
      ),
      drawer: isWide ? null : const Drawer(child: _SideNav(compact: false)),
    );
  }
}

class _SideNav extends StatelessWidget {
  final bool compact;
  const _SideNav({this.compact = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 260,
      color: AppTheme.primary,
      padding: const EdgeInsets.all(20),
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                CircleAvatar(backgroundColor: Colors.white, child: Icon(Icons.health_and_safety, color: AppTheme.primary)),
                SizedBox(width: 12),
                Expanded(child: Text('FMD AI Surveillance', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold))),
              ],
            ),
            const SizedBox(height: 32),
            _navItem(context, Icons.dashboard_outlined, 'Dashboard', '/'),
            _navItem(context, Icons.add_a_photo_outlined, 'New Analysis', '/analysis'),
            _disabledItem(Icons.map_outlined, 'Outbreak Map'),
            _disabledItem(Icons.description_outlined, 'Reports'),
            _disabledItem(Icons.settings_outlined, 'Settings'),
            const Spacer(),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: Colors.white.withOpacity(.12), borderRadius: BorderRadius.circular(16)),
              child: const Text('DenseNet cattle validation + EfficientNetB3 FMD classifier + Random Forest decision fusion.', style: TextStyle(color: Colors.white70, height: 1.4)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _navItem(BuildContext context, IconData icon, String label, String route) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        leading: Icon(icon, color: Colors.white),
        title: Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
        onTap: () => Navigator.pushNamed(context, route),
      ),
    );
  }

  Widget _disabledItem(IconData icon, String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        leading: Icon(icon, color: Colors.white.withOpacity(.6)),
        title: Text(label, style: TextStyle(color: Colors.white.withOpacity(.6), fontWeight: FontWeight.w600)),
      ),
    );
  }
}
