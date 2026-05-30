import 'dart:io' show File;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/professional_shell.dart';
import 'result_screen.dart';

class AnalysisScreen extends StatefulWidget {
  const AnalysisScreen({super.key});

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  final _formKey = GlobalKey<FormState>();

  final _farmerName = TextEditingController();
  final _farmName = TextEditingController();
  final _district = TextEditingController(text: 'Soroti');
  final _subcounty = TextEditingController();
  final _village = TextEditingController();
  final _phone = TextEditingController();
  final _duration = TextEditingController();
  final _temperature = TextEditingController();

  final Map<String, bool> symptoms = {
    'fever': false,
    'mouth_lesions': false,
    'drooling': false,
    'lameness': false,
    'loss_of_appetite': false,
    'hoof_lesions': false,
    'reduced_milk': false,
  };

  File? selectedImage;
  Uint8List? selectedImageBytes;
  String? selectedImageName;

  bool loading = false;

  bool get requiredSymptomsCaptured {
    return symptoms.values.any((v) => v) && _duration.text.trim().isNotEmpty;
  }

  bool get imageSelected => selectedImageBytes != null;

  Future<void> pickImage(ImageSource source) async {
    if (!_formKey.currentState!.validate() || !requiredSymptomsCaptured) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Complete mandatory farm details and symptoms before photo analysis.',
          ),
        ),
      );
      return;
    }

    final picked = await ImagePicker().pickImage(
      source: source,
      imageQuality: 85,
    );

    if (picked != null) {
      final bytes = await picked.readAsBytes();

      setState(() {
        selectedImageBytes = bytes;
        selectedImageName = picked.name;
        selectedImage = kIsWeb ? null : File(picked.path);
      });
    }
  }

  Future<void> submit() async {
    if (!_formKey.currentState!.validate() ||
        !requiredSymptomsCaptured ||
        !imageSelected) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Complete farm details, symptoms, and photo before analysis.',
          ),
        ),
      );
      return;
    }

    setState(() => loading = true);

    try {
      final farmInfo = {
        'farmer_name': _farmerName.text.trim(),
        'farm_name': _farmName.text.trim(),
        'district': _district.text.trim(),
        'subcounty': _subcounty.text.trim(),
        'village': _village.text.trim(),
        'phone': _phone.text.trim(),
      };

      final symptomPayload = {
        ...symptoms.map((key, value) => MapEntry(key, value ? 1 : 0)),
        'duration_days': int.tryParse(_duration.text.trim()) ?? 0,
        'temperature': double.tryParse(_temperature.text.trim()) ?? 0,
      };

      final result = await ApiService.analyzeCattle(
        image: selectedImage,
        imageBytes: selectedImageBytes!,
        imageName: selectedImageName ?? 'cattle_photo.jpg',
        farmInfo: farmInfo,
        symptoms: symptomPayload,
      );

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultScreen(result: result),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  void dispose() {
    _farmerName.dispose();
    _farmName.dispose();
    _district.dispose();
    _subcounty.dispose();
    _village.dispose();
    _phone.dispose();
    _duration.dispose();
    _temperature.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ProfessionalShell(
      title: 'New Cattle Analysis',
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          onChanged: () => setState(() {}),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _instructionBanner(),
              const SizedBox(height: 18),
              LayoutBuilder(
                builder: (context, c) {
                  final wide = c.maxWidth > 900;

                  return wide
                      ? Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(child: _farmCard()),
                            const SizedBox(width: 18),
                            Expanded(child: _symptomCard()),
                          ],
                        )
                      : Column(
                          children: [
                            _farmCard(),
                            const SizedBox(height: 18),
                            _symptomCard(),
                          ],
                        );
                },
              ),
              const SizedBox(height: 18),
              _photoCard(),
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: loading || !imageSelected ? null : submit,
                  icon: loading
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.health_and_safety_outlined),
                  label: Text(
                    loading ? 'Analyzing...' : 'Run Hybrid FMD Analysis',
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _instructionBanner() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.primary.withOpacity(.08),
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Row(
        children: [
          Icon(Icons.info_outline, color: AppTheme.primary),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'Farm location, farmer identity and clinical signs are mandatory. '
              'Photo analysis is enabled only after the form is complete.',
            ),
          ),
        ],
      ),
    );
  }

  Widget _farmCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Mandatory Farm Information',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 14),
            _text(_farmerName, 'Farmer name *'),
            _text(_farmName, 'Farm name *'),
            _text(_district, 'District *'),
            _text(_subcounty, 'Sub-county *'),
            _text(_village, 'Village *'),
            _text(_phone, 'Phone number'),
          ],
        ),
      ),
    );
  }

  Widget _symptomCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Mandatory Clinical Signs & Symptoms',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 8),
            const Text('Select all observed signs before capturing the image.'),
            const SizedBox(height: 10),
            ...symptoms.keys.map(
              (key) => SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(key.replaceAll('_', ' ').toUpperCase()),
                value: symptoms[key]!,
                onChanged: (v) => setState(() => symptoms[key] = v),
              ),
            ),
            _text(
              _duration,
              'Duration of symptoms in days *',
              keyboard: TextInputType.number,
            ),
            _text(
              _temperature,
              'Temperature if available',
              keyboard: TextInputType.number,
            ),
          ],
        ),
      ),
    );
  }

  Widget _photoCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Cattle Photo Evidence',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              requiredSymptomsCaptured
                  ? 'Photo capture is enabled.'
                  : 'Complete symptoms first to enable photo analysis.',
              style: TextStyle(
                color: requiredSymptomsCaptured
                    ? AppTheme.success
                    : AppTheme.danger,
              ),
            ),
            const SizedBox(height: 12),
            if (selectedImageBytes != null)
              ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: kIsWeb
                    ? Image.memory(
                        selectedImageBytes!,
                        height: 220,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      )
                    : Image.file(
                        selectedImage!,
                        height: 220,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),
              ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                OutlinedButton.icon(
                  onPressed: requiredSymptomsCaptured
                      ? () => pickImage(ImageSource.camera)
                      : null,
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: const Text('Capture Photo'),
                ),
                OutlinedButton.icon(
                  onPressed: requiredSymptomsCaptured
                      ? () => pickImage(ImageSource.gallery)
                      : null,
                  icon: const Icon(Icons.upload_file_outlined),
                  label: const Text('Upload Photo'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _text(
    TextEditingController controller,
    String label, {
    TextInputType keyboard = TextInputType.text,
  }) {
    final required = label.contains('*');

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboard,
        decoration: InputDecoration(labelText: label),
        validator: required
            ? (v) => v == null || v.trim().isEmpty ? 'Required' : null
            : null,
      ),
    );
  }
}
